#!/usr/bin/python

import logging
import math
import os
import random
import socket
import sys
import thread
import threading
import time
import uuid

from hostmap15 import NEIGHBORS_MAP

# Local name for LOG
LOG_NAME = ''
LOG_FILE = ''


## ACE Messages
ACE_MSG_GETSTATUS = 0
ACE_MSG_RECRUIT = 1
ACE_MSG_POLL = 2
ACE_MSG_PROMOTE = 3
ACE_MSG_ABDICATE = 4
ACE_MSG_PROMOTE_DONE = 5
ACE_MSG_POLL_OK = 6
ACE_MSG_POLL_NA = 7
ACE_MSG_LEADER_ANNOUNCEMENT = 8
# Description of Messages
ACE_MSG_STR = ['ACE_MSG_GETSTATUS',
               'ACE_MSG_RECRUIT',
               'ACE_MSG_POLL',
               'ACE_MSG_PROMOTE',
               'ACE_MSG_ABDICATE',
               'ACE_MSG_PROMOTE_DONE',
               'ACE_MSG_POLL_OK',
               'ACE_MSG_POLL_NA',
               'ACE_MSG_LEADER_ANNOUNCEMENT']

## ACE States
ACE_STATE_UNCLUSTERED = 0
ACE_STATE_CLUSTERED = 1
ACE_STATE_CLUSTER_HEAD = 2
## Description for states
ACE_STATE_STR = ['ACE_STATE_UNCLUSTERED',
                 'ACE_STATE_CLUSTERED',
                 'ACE_STATE_CLUSTER_HEAD']

## ACE Parameters
ACE_MAX_WAIT_TIME = 2500.0                                  # milisseconds
ACE_EXPECTED_ROUNDS = 4                                     # number of rounds to run
ACE_EXPECTED_ITERATION_LENGHT = 1.5                         # seconds
ITERATION_INTERVAL = 200 + random.randrange(0, ACE_MAX_WAIT_TIME) # Interval between iterations

# Estimated node degree
ACE_K1 = 2.3                                                # Values from the authors of the ACE
ACE_K2 = 0.08                                               # Values from the authors of the ACE
ACE_D = sum([len(NEIGHBORS_MAP[node]) for node in NEIGHBORS_MAP]) / len(NEIGHBORS_MAP)
ACE_CI = (ACE_MAX_WAIT_TIME/1000) * ACE_EXPECTED_ROUNDS # Estimated duration of the ACE

## Socket Parameters
TCP_SERVER_PORT = 40000
TCP_BUFFER_SIZE = 2048
UDP_SERVER_PORT = 39999
TCP_TIMEOUT = 10
TCP_MAX_ATTEMPS = 3


def of_set_controller(bridge_name='ap1', controller_ip='127.0.0.1', controller_port='6653'):
    set_command = 'ovs-vsctl --db=unix:/var/run/openvswitch/db.sock set-controller '
    set_command = set_command + bridge_name + ' '
    set_command = set_command + ' tcp:' + controller_ip + ':' + controller_port
    os.system(set_command)


def of_del_controller(bridge_name='ap1'):
    set_command = 'ovs-vsctl --db=unix:/var/run/openvswitch/db.sock del-controller '
    set_command = set_command + bridge_name
    os.system(set_command)


class SimpleNode(object):


    def __init__(self, node_address):
        self.node_address = node_address    # the node address (IP address in the simulation)
        self.is_cluster_head = False        # true when the node is a Cluster Head
        self.loyal_followers = set()        # set of loyal followers of the node
        self.cluster_membership = dict()    # a dict of clusters to follow
        self.migrating = False              # flag to control PROMOTE process
        self.migrating_to = ''              # the address of the new leader node
        self.ace_done = False               # flag to control whether the election is done
        self.my_cluster_id = ''             # node cluster DI when the node is a CH
        self.total_iters = 0                # stores the total number of iteractions
        self.current_controller = ()        # current SND Controller. Tuple: (<ip>, followers)

        ## Initializing the listener
        self.handle_connections_t = threading.Thread(target=self.handle_client_connection, args=())
        self.handle_connections_t.daemon = True
        self.handle_connections_t.start()

        ## Initializing the listener for leader annoucement (UDP)
        self.handle_leader_announcement_t = threading.Thread(target=self.handle_leader_announcement, args=())
        self.handle_leader_announcement_t.daemon = True
        self.handle_leader_announcement_t.start()

        self.start_time = time.time()       # the start time of the algorithm
        ## Printing the host name arg
        logging.info("---- Starting ACE algorithm for CH. The node address is %s",
                     self.node_address)
        logging.info("---- The iteration interval is %s ms.",
                     ITERATION_INTERVAL)
        time.sleep(0.400)
        self.start_ace()


    def join_cluster(self, cluster_id, ch_address=''):
        # if cluster_id not in self.cluster_membership:
        self.cluster_membership[cluster_id] = ch_address
        logging.debug("Node joined new cluster. Cluster=%s; Head=%s", cluster_id, ch_address)


    def left_cluster(self, cluster_id, ch_address):
        if cluster_id in self.cluster_membership:
            existing_ch_address = self.cluster_membership[cluster_id]
            if existing_ch_address == ch_address:
                del self.cluster_membership[cluster_id]
                logging.debug("Node left Cluster=%s; Head=%s", cluster_id, ch_address)
        else:
            logging.debug('Node isn\'t a member of the cluster. Cluster=%s.', cluster_id)


    def get_cluster_head(self, search_id):
        address_found = ''
        for cluster_id, head_ip in self.cluster_membership.iteritems():
            if search_id == cluster_id:
                address_found = head_ip
        return address_found


    def set_cluster_head(self, cluster_id, new_ch_address):
        if cluster_id in self.cluster_membership:
            old_address = self.cluster_membership[cluster_id]
            self.cluster_membership[cluster_id] = new_ch_address
            logging.info('CH updated! Cluster=%s; Old head=%s; New Head=%s',
                         cluster_id, old_address, new_ch_address)
        else:
            logging.debug('Failed to update cluster head. Node isn\'t a member of Cluster=%s',
                          cluster_id)


    def get_mystate(self):
        if self.is_cluster_head:
            return ACE_STATE_CLUSTER_HEAD
        else:
            if len(self.cluster_membership) > 0:
                return ACE_STATE_CLUSTERED
            else:
                return ACE_STATE_UNCLUSTERED


    @classmethod
    def fmin(cls, my_time, ace_ci):
        result = (math.exp(-ACE_K1 * my_time/ace_ci) - ACE_K2) * ACE_D
        return result


    def generate_new_random_id(self):
        return str(uuid.uuid4())[:8]


    def get_loyal_followers(self):
        return len(self.loyal_followers)


    def start_ace(self):
        self.total_iters = 0
        while not self.ace_done:
            time.sleep(ITERATION_INTERVAL / 1000.0)
            logging.info("ACE Iteration %s", self.total_iters)
            self.scale_one_iteraction()
            self.total_iters = self.total_iters + 1


    def scale_one_iteraction(self):
        num_loyal_followers = self.count_loyal_followers()
        my_time = time.time() - self.start_time
        if my_time > (3 * ACE_EXPECTED_ITERATION_LENGHT):
            # Set the flag to stop the algorithm
            if not self.migrating:
                self.ace_done = True
            if self.get_mystate() == ACE_STATE_CLUSTER_HEAD:
                print "+---------------------------------+"
                print "|       Node elected as CH        |"
                print "+---------------------------------+"
                self.send_leader_announcement(self.node_address,
                                              self.my_cluster_id,
                                              self.get_loyal_followers())
            elif self.get_mystate() == ACE_STATE_CLUSTERED:
                # pick one as my cluster-head
                print "+---------------------------------+"
                print "|   Pick one as my cluster-head   |"
                print "+---------------------------------+"
            elif self.get_mystate() == ACE_STATE_UNCLUSTERED:
                # pick a random clustered node to as proxy
                # after it terminates wait for it to terminate
                print "+---------------------------------+"
                print "| Node will declare himself as CH |"
                print "+---------------------------------+"
            # Print the node info for debug purpose
            file_content = "NODE;{0:s};STATE;{1:s};TOTAL_ITER;{2:s};TIME;{3:s}\n"
            file_content = file_content.format(
                self.node_address,
                str(self.get_mystate()),
                str(self.total_iters),
                str(my_time))
            log_file = open(LOG_NAME, 'a')
            log_file.write(file_content)
            log_file.close()
            self.print_node_info()
        else:
            # State: UNCLUSTERED
            if self.get_mystate() == ACE_STATE_UNCLUSTERED and \
                    num_loyal_followers >= self.fmin(my_time, ACE_CI):
                self.my_cluster_id = self.generate_new_random_id()
                logging.info("Node %s will spawn a new CH with ID %s.",
                             self.node_address, self.my_cluster_id)
                self.is_cluster_head = True
                self.locally_broadcast(ACE_MSG_RECRUIT, self.node_address, self.my_cluster_id)

            # State: CLUSTER_HEAD
            if self.get_mystate() == ACE_STATE_CLUSTER_HEAD:
                # The node prepares to migrate its cluster
                logging.info("The Node is preparing to MIGRATE its cluster.")
                best_leader = self.node_address
                best_follower_count = num_loyal_followers
                # Polls all neighbors to find the best candidate
                for neighbor_address in NEIGHBORS_MAP[self.node_address]:
                    follower_count = self.poll_for_num_loyal_followers(neighbor_address,
                                                                       self.my_cluster_id)
                    # the node answer the POLL message with ACE_MSG_POLL_NA
                    if follower_count == -1:
                        continue
                    # normal answer
                    if follower_count > best_follower_count:
                        best_leader = neighbor_address
                        best_follower_count = follower_count
                if best_leader != self.node_address:
                    logging.info("Node %s will be a best leader candidate.", best_leader)
                    # promote the best candidate found (and set migrating flag to True)
                    self.send_promote_message(best_leader, ACE_MSG_PROMOTE, self.my_cluster_id)
                    ## wait for the bestLeader to broadcast RECRUIT message
                    while self.migrating:
                        logging.debug("Waiting for node %s to send its RECRUIT message...",
                                      best_leader)
                        time.sleep(0.100)
                    self.locally_broadcast(ACE_MSG_ABDICATE, self.node_address, self.my_cluster_id)
                    logging.info("I will ABDICATE as leader of Cluster=%s", self.my_cluster_id)
                    self.my_cluster_id = ''
                else:
                    logging.info("I'm the best leader. I decided not to migrate the CH.")


    def send_promote_done(self, target_address):
        logging.debug("Sending PROMOTE_DONE message to node %s", target_address)
        message_to_send = ';'.join([str(ACE_MSG_PROMOTE_DONE)])
        try:
            self.send_message_noans(target_address, message_to_send)
        except socket.error, exc:
            logging.error("Could not send PROMOTE_DONE to node %s. Exception: %s",
                          target_address, exc)


    def send_promote_message(self, target_address, ace_msg, cluster_id):
        logging.debug("Sending PROMOTE message to node %s", target_address)
        promote_messsage = ';'.join([str(ace_msg), cluster_id])
        self.migrating = True
        self.migrating_to = target_address
        try:
            self.send_message_noans(target_address, promote_messsage)
            logging.debug('Waiting for the node %s to broadcast RECRUIT message.', target_address)
        except socket.error, exc:
            logging.error("Could not send MIGRATE to node %s. Error: %s", target_address, exc)
            self.migrating = False
            self.migrating_to = ''
        return


    def poll_for_num_loyal_followers(self, neighbor_address, cluster_id):
        logging.debug("POLLING the number of loyal followers of node %s. Cluster=%s",
                      neighbor_address, cluster_id)
        poll_messsage = ';'.join([str(ACE_MSG_POLL), cluster_id])
        data_arr = self.send_message(neighbor_address, poll_messsage)
        logging.debug("POLLING: Received message was: %s", data_arr)
        response_status = int(data_arr[0])
        neighbohr_loyal_followers = int(data_arr[1])
        if response_status == ACE_MSG_POLL_OK:
            logging.debug('POLL: Host %s has %s loyal follwoers with id %s',
                          neighbor_address, neighbohr_loyal_followers, cluster_id)
            return neighbohr_loyal_followers
        else:
            return -1


    def count_loyal_followers(self, poll_id=''):
        # if poll_id is not empty the request came from a POLL_REQ
        local_request = poll_id == ''
        poller_followers = set()
        if local_request:
            self.loyal_followers.clear()
            logging.debug("LOYALFOLLOWERS: Counting the number of loyal followers.")
        else:
            poller_followers.clear()
            logging.debug("LOYALFOLLOWERS: Counting the number of loyal followers \
                           from a POLL message. Cluster=%s", poll_id)
        # traverse the list of neighbors of the node
        for neighbor_address in NEIGHBORS_MAP[self.node_address]:
            message_to_send = str(ACE_MSG_GETSTATUS)
            # The GETSTATUS will always return a 3 elements array
            data_array = self.send_message(neighbor_address, message_to_send)
            logging.debug('LOYALFOLLOWERS: Answer from host %s: %s', neighbor_address, data_array)
            neighbor_state = int(data_array[0])
            neighbor_ch_count = int(data_array[1])
            neighbor_cluster_id = str(data_array[2])
            if local_request:
                # processing code for a local request
                if neighbor_state == ACE_STATE_UNCLUSTERED:
                    # if the neighbor is Unclustered, it will be a loyal follower
                    self.loyal_followers.add(neighbor_address)
                if neighbor_state == ACE_STATE_CLUSTERED:
                    # if the neighbor is Clustered, it follow only one node
                    if neighbor_ch_count == 1 and neighbor_cluster_id == self.my_cluster_id:
                        self.loyal_followers.add(neighbor_address)
            else:
                if neighbor_state == ACE_STATE_UNCLUSTERED:
                    # if the neighbor is Unclustered, it will be a loyal follower
                    poller_followers.add(neighbor_address)
                if neighbor_state == ACE_STATE_CLUSTERED:
                    # it is only a loyal follower if the neighbor is already in the cluster
                    if neighbor_ch_count == 1 and neighbor_cluster_id == poll_id:
                        poller_followers.add(neighbor_address)
        if local_request:
            n_loyal_followers = len(self.loyal_followers)
            logging.debug("I have %s loyal followres.", n_loyal_followers)
        else:
            n_loyal_followers = len(poller_followers)
            logging.debug("I have %s nighbors followres of CH=%s.",
                          n_loyal_followers, poll_id)
        return n_loyal_followers


    def locally_broadcast(self, ace_msg, node_address, cluster_id):
        for neighbor_address in NEIGHBORS_MAP[self.node_address]:
            logging.debug("Sending %s message to node: %s",
                          ACE_MSG_STR[ace_msg], neighbor_address)
            message = ';'.join([str(ace_msg), node_address, cluster_id])
            self.send_message_noans(neighbor_address, message)


    def send_message(self, dst_address, message_str):
        dst_port = TCP_SERVER_PORT + int(dst_address.split('.')[3])
        logging.debug("send_message: node %s message %s", dst_address, message_str)
        response_arr = []
        for attemp in range(TCP_MAX_ATTEMPS):
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.settimeout(TCP_TIMEOUT)
            try:
                send_socket.connect((dst_address, dst_port))
                send_socket.send(message_str)
                response_str = send_socket.recv(TCP_BUFFER_SIZE)
                response_arr = response_str.split(';')
                send_socket.close()
            except socket.timeout:
                logging.error("send_message: Socket timeout error. Attemp %s", attemp)
                time.sleep(0.5)
                continue
            except socket.error, exc:
                logging.critical("send_message: error sending message to node %s. Exception: %s",
                                 dst_address, exc)
                raise
            else:
                break
        return response_arr


    def send_message_noans(self, dst_address, message_str):
        dst_port = TCP_SERVER_PORT + int(dst_address.split('.')[3])
        logging.debug("send_message_noans: node %s message %s", dst_address, message_str)
        for attemp in range(TCP_MAX_ATTEMPS):
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.settimeout(TCP_TIMEOUT)
            try:
                send_socket.connect((dst_address, dst_port))
                send_socket.send(message_str)
                send_socket.close()
            except socket.timeout:
                logging.error("send_message: Socket timeout error. Attemp %s", attemp)
                time.sleep(0.5)
            except socket.error, exc:
                logging.critical("send_message_noans: error sending message to node %s. \
                                 Exception: %s", dst_address, exc)
                raise
            else:
                break
        return


    def handle_client_connection(self):
        local_port = TCP_SERVER_PORT + int(self.node_address.split('.')[3])
        logging.debug("CONNHANDLER: Handling client connections...")
        logging.debug("CONNHANDLER: Binding on IP: %s Port: %s.",
                      self.node_address, local_port)
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.bind((self.node_address, local_port))
        tcp_socket.listen(1)
        while True:
            (conn, client) = tcp_socket.accept()
            thread.start_new_thread(self.client_connection, tuple([conn, client]))
        # tcp_socket.close()


    def client_connection(self, client_sock, client_address):
        logging.debug("CLIENT_CONN: Connected by: %s:%s",
                      client_address[0], client_address[1])
        while True:
            request = client_sock.recv(TCP_BUFFER_SIZE)
            # No request sent by the client
            if not request: 
                break

            # Normal processing of the request
            ace_msg = int(request.split(';')[0])
            logging.debug("CLIENT_CONN: Receiving message: %s from host %s",
                          ACE_MSG_STR[ace_msg], client_address[0])

            # ACE_MSG_GETSTATUS
            if ace_msg == ACE_MSG_GETSTATUS:
                # The response should include
                # staus, number of clusters, cluster id (when following one cluster only)
                r_state = str(self.get_mystate())
                r_number_of_chs = str(len(self.cluster_membership))
                r_cluster_id = ''
                if len(self.cluster_membership) == 1:
                    r_cluster_id = self.cluster_membership.keys()[0]
                response_str = ';'.join([r_state, r_number_of_chs, r_cluster_id])
                logging.debug("CLIENT_CONN: Sending message %s to node %s", response_str,
                              client_address[0])
                client_sock.send(response_str)

            # ACE_MSG_RECRUIT
            if ace_msg == ACE_MSG_RECRUIT:
                new_ch_address = request.split(';')[1]
                new_cluster_id = request.split(';')[2]
                # Disable the migrating flag soon as the node receive a RECRUIT message
                # from the node that it is migrating to
                if self.migrating and self.migrating_to == new_ch_address:
                    self.migrating = False
                    self.migrating_to = ''
                    self.is_cluster_head = False
                # Normal processing of a RECRUIT MSG
                if self.get_mystate() == ACE_STATE_CLUSTER_HEAD:
                    logging.info("CLIENT_CONN: I am a CH. I will not follow %s.",
                                 new_ch_address)
                else:
                    self.join_cluster(new_cluster_id, new_ch_address)
                    logging.info("CLIENT_CONN: OK! I am a follower of the CH %s",
                                 new_ch_address)

            # ACE_MSG_POLL
            if ace_msg == ACE_MSG_POLL:
                response_str = ''
                if not self.ace_done:
                    ch_to_poll = request.split(';')[1]
                    num_loyal_followers = self.count_loyal_followers(ch_to_poll)
                    # num_loyal_followers = str(len(self.loyal_followers))
                    # Not used anymore
                    r_status = str(ACE_MSG_POLL_OK)
                    r_num_loyal_followers = str(num_loyal_followers)
                    response_str = ';'.join([r_status, r_num_loyal_followers])
                    logging.debug("CLIENT_CONN: POLL Done! The answer was sent.")
                else:
                    r_status = str(ACE_MSG_POLL_NA)
                    r_num_loyal_followers = str(0)
                    response_str = ';'.join([r_status, r_num_loyal_followers])
                    logging.debug("CLIENT_CONN: POLL NA!")
                client_sock.send(response_str)

            # ACE_MSG_PROMOTE
            if ace_msg == ACE_MSG_PROMOTE:
                cluster_id = request.split(';')[1]
                self.is_cluster_head = True
                self.my_cluster_id = cluster_id
                self.locally_broadcast(ACE_MSG_RECRUIT, self.node_address, cluster_id)
                self.send_promote_done(client_address[0])

            # ACE_MSG_PROMOTE_DONE
            if ace_msg == ACE_MSG_PROMOTE_DONE:
                self.migrating = False
                self.migrating_to = ''

            # ACE_MSG_ABDICATE
            if ace_msg == ACE_MSG_ABDICATE:
                ch_address = request.split(';')[1]
                cluster_id = request.split(';')[2]
                self.left_cluster(cluster_id, ch_address)
        
        logging.debug("CLIENT_CONN: Closing client connection: %s:%s",
                      client_address[0], client_address[1])
        client_sock.close()
        thread.exit()


    def send_leader_announcement(self, node_address, cluster_id, num_loyal_followers):
        self.leader_update(node_address, int(num_loyal_followers))
        message = ';'.join([str(ACE_MSG_LEADER_ANNOUNCEMENT),
                            str(node_address),
                            str(cluster_id),
                            str(num_loyal_followers)])
        bcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        bcast_socket.settimeout(0.5)
        bcast_socket.bind((self.node_address, UDP_SERVER_PORT - 1))
        bcast_socket.sendto(message, ('<broadcast>', UDP_SERVER_PORT))
        bcast_socket.close()
        logging.info("Leader announcement sent!")


    def handle_leader_announcement(self):
        bcast_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bcast_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        bcast_client.bind(('', UDP_SERVER_PORT))
        logging.info("BCAST: Binding port for leader announcement")
        while True:
            (data, addr) = bcast_client.recvfrom(2048)
            logging.info("BCAST: Recv leader announcement.")
            thread.start_new_thread(self.leader_announcement, tuple([data, addr]))
        bcast_client.close()


    def leader_announcement(self, data, client_address):
        logging.debug("LEADER_ANN: Sending leader announcement.")
        ace_msg = int(data.split(';')[0])
        if ace_msg == ACE_MSG_LEADER_ANNOUNCEMENT:
            announced_leader_addr = data.split(';')[1]
            announced_leader_flw = int(data.split(';')[3])
            self.leader_update(announced_leader_addr, announced_leader_flw)


    def leader_update(self, address, followers):
        logging.debug("LEADER_UPD: Setting to: %s", address)
        new_addr = address
        new_flw = followers
        update = False

        if len(self.current_controller) == 0:
            self.current_controller = (new_addr, new_flw)
            of_set_controller('ap1', '127.0.0.1', '6653')
            logging.debug("")
        else:
            curr_addr, curr_flw = self.current_controller
            # new controller has a greater number of followers
            if new_flw > curr_flw:
                update = True
            # same number of followers, use the last octet of the address
            if new_flw == curr_flw:
                curr_last_octect = int(curr_addr.split('.')[3])
                new_last_octect = int(new_addr.split('.')[3])
                if new_last_octect > curr_last_octect:
                    update = True
            if update:
                self.current_controller = (new_addr, new_flw)
                # just for simulation
                if self.node_address == '10.0.0.1':
                    logging.debug("LEADER_UPD: Configuring OVS to: %s", address)
                    of_del_controller('ap1')
                    of_set_controller('ap1', '127.0.0.1', '6653')


    def __str__(self):
        return "Node <iii> state: " + self.get_mystate() + "\n"


    def print_node_info(self, fmin=0):
        print " Node Info:"
        print "  - IP: %s" % self.node_address
        print "  - State: %s" % ACE_STATE_STR[self.get_mystate()]
        print "  - Time running ACE: %.3f" % (time.time() - self.start_time)
        print "  - CH id: %s" % self.my_cluster_id
        if fmin != 0:
            print "  - F_min: %f" % fmin
        self.print_chs()
        self.print_loyal_followers()


    def print_chs(self):
        print "+--------------------------------+"
        print "|       Clusters table           |"
        print "+--------------------------------+"
        for cluster_id, ch_address in self.cluster_membership.iteritems():
            print "| %-15s -> %11s |" % (cluster_id, ch_address)
        print "+--------------------------------+"
        print ""


    def print_loyal_followers(self):
        print "+--------------------------------+"
        print "|     Loyal Followers table      |"
        print "+--------------------------------+"
        for follower in self.loyal_followers:
            print "| %-30s |" % follower
        print "+--------------------------------+"
        print ""


def main(host_ip, log_level):
    # check the parameter format. It should be an Ip ADDRESS
    if host_ip not in NEIGHBORS_MAP:
        raise Exception("Wrong host IP address.")
    ## Setting up the log system
    # log_format = "%(asctime)s: %(funcName)20s() - %(lineno)s: %(message)s"
    log_format = "%(asctime)s,%(msecs)03d:L%(lineno)4s: %(message)s"
    logging.basicConfig(level=log_level,
                        format=log_format,
                        datefmt='%H:%M:%S',)
    simple_node = SimpleNode(host_ip)

if __name__ == '__main__':
    HOST_IP = str(sys.argv[1])
    NODE_NUMBER = sys.argv[3].zfill(2)
    LOG_NAME = "nodes{0:2s}.log".format(NODE_NUMBER)
    main(HOST_IP, logging.INFO)
    time.sleep(10)

#!/usr/bin/python

import inspect
import logging
import math
import random
import socket
import sys
import threading
import time
import uuid

NEIGHBORS_MAP = {
    "10.0.0.1": ['10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.5', '10.0.0.6', '10.0.0.8'],
    "10.0.0.2": ['10.0.0.3', '10.0.0.1', '10.0.0.9'],
    "10.0.0.3": ['10.0.0.4', '10.0.0.1', '10.0.0.2'],
    "10.0.0.4": ['10.0.0.3', '10.0.0.5', '10.0.0.1'],
    "10.0.0.5": ['10.0.0.4', '10.0.0.6', '10.0.0.1'],
    "10.0.0.6": ['10.0.0.1', '10.0.0.5', '10.0.0.7', '10.0.0.8'],
    "10.0.0.7": ['10.0.0.8', '10.0.0.6'],
    "10.0.0.8": ['10.0.0.1', '10.0.0.6', '10.0.0.7', '10.0.0.9'],
    "10.0.0.9": ['10.0.0.2', '10.0.0.8']
}


## ACE Messages
ACE_MSG_GETSTATUS = 0
ACE_MSG_RECRUIT = 1
ACE_MSG_POLL = 2
ACE_MSG_PROMOTE = 3
ACE_MSG_ABDICATE = 4

ACE_MSG_PROMOTE_WAIT = 8
ACE_MSG_PROMOTE_DONE = 9

## ACE States
ACE_STATE_UNCLUSTERED = 0
ACE_STATE_CLUSTERED = 1
ACE_STATE_CLUSTER_HEAD = 2
## Description for states
ACE_STATE_STR = ['ACE_STATE_UNCLUSTERED', 'ACE_STATE_CLUSTERED', 'ACE_STATE_CLUSTER_HEAD']

## ACE Parameters
ACE_MAX_WAIT_TIME = 3000     # milisseconds
ACE_EXPECTED_DURATION_LENGHT = 7        # milisseconds
ACE_K1 = 2.3                            # Values from the authors of the ACE
ACE_K2 = 0.1                            # Values from the authors of the ACE
# Estimated node degree
ACE_D = sum ([ len(NEIGHBORS_MAP[node]) for node in NEIGHBORS_MAP ]) / len(NEIGHBORS_MAP)
CI = 30                                 # Estimated duration of the ACE

## Socket Parameters
TCP_SERVER_PORT = 50005
# TCP_CLIENT_PORT = 50006
TCP_BUFFER_SIZE = 2048
TCP_TIMEOUT = 10
TCP_MAX_ATTEMPS = 3

class SimpleNode(object):
    loyal_followers_list = set()
    num_loyal_followers = 0
    cluster_to_follow = ''


    def __init__(self, node_address):
        self.my_cluster_id = ''
        self.my_ip = node_address
        self.my_state = ACE_STATE_UNCLUSTERED
        self.start_time = time.time()
        self.cluster_head_list = []
        ## adittional flag to control PROMOTE process
        self.migrating = False
        ## Initializing the listener
        self.handle_connections_t = threading.Thread(target=self.handle_client_connection, args=())
        self.handle_connections_t.daemon = True
        self.handle_connections_t.start()
        ## Printing the host name arg
        logging.debug("Starting ACE algorithm for CH. The node address is %s", self.my_ip)
        self.start_ace()


    def add_cluster_head(self, ch_ip, ch_id):
        pass


    def del_cluster_head(self, ch_ip):
        pass


    def get_mystate(self):
        return self.my_state


    @classmethod
    def fmin(cls, my_time, cI):
        result = (math.exp(-ACE_K1 * my_time/cI) - ACE_K2) * ACE_D
        return result


    def generate_new_random_id(self):
        return str(uuid.uuid4())[:8]


    def get_num_loyal_followers(self):
        return len(self.loyal_followers_list)


    def start_ace(self):
        logging.debug("Starting the ACE algorithm...")
        time_delay = random.randrange(0, ACE_MAX_WAIT_TIME)
        logging.debug("The waiting time is %s ms.", time_delay)
        time.sleep(time_delay / 1000.0)
        for i in range(10):
            print "--------------------------------------------------------------------"
            print "  ACE: Iteration %s" % i
            self.scale_one_iteraction()
            time.sleep(3)


    def scale_one_iteraction(self):
        self.num_loyal_followers = self.count_loyal_followers()
        my_time = time.time() - self.start_time
        self.print_node_info(self.fmin(my_time, CI))
        if my_time > (3 * ACE_EXPECTED_DURATION_LENGHT):
            if self.my_state == ACE_STATE_CLUSTER_HEAD:
                print "+--------------------------------+"
                print "|      Node elected as CH        |"
                print "+--------------------------------+"
            elif self.my_state == ACE_STATE_CLUSTERED:
                # pick one as my cluster-head
                print "+--------------------------------+"
                print "|   Pick one as my cluster-head  |"
                print "+--------------------------------+"
            elif self.my_state == ACE_STATE_UNCLUSTERED:
                # pick a random clustered node to as proxy
                # after it terminates wait for it to terminate
                print "+--------------------------------+"
                print "|    Node will declare himself   |"
                print "|             as CH              |"
                print "+--------------------------------+"
        elif self.my_state == ACE_STATE_UNCLUSTERED and \
                self.num_loyal_followers >= self.fmin(my_time, CI):
            self.my_cluster_id = self.generate_new_random_id()
            self.my_state = ACE_STATE_CLUSTER_HEAD
            logging.info("Node %s will spawn a new CH with ID %s.", self.my_ip, self.my_cluster_id)
            self.locally_broadcast(ACE_MSG_RECRUIT, self.my_ip, self.my_cluster_id)
        elif self.my_state == ACE_STATE_CLUSTER_HEAD:
            # The node prepares to migrate its cluster
            best_leader = self.my_cluster_id
            best_follower_count = self.num_loyal_followers
            # Polls all neighbors to find the best candidate
            for neighbor_address in NEIGHBORS_MAP[self.my_ip]:
                follower_count, n = self.poll_for_num_loyal_followers(neighbor_address,
                                                                      self.my_cluster_id)
                if follower_count > best_follower_count:
                    best_leader = n
                    best_follower_count = follower_count
                    best_leader_address = neighbor_address
            if best_leader != self.my_cluster_id:
                ## update my status to clustered
                ## add the new cluster leader to the list
                self.send_promote_message(best_leader_address, ACE_MSG_PROMOTE, self.my_cluster_id)
                ## wait for the bestLeader to broadcast RECRUIT message
                while self.migrating:
                    logging.debug("Waiting for node %s to send its RECRUIT message...",
                                  best_leader_address)
                    time.sleep(0.250)
                self.locally_broadcast(ACE_MSG_ABDICATE, self.my_ip, self.my_cluster_id)
        self.print_node_info()


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
        try:
            self.send_message_noans(target_address, promote_messsage)
            logging.debug('Waiting for the node %s to broadcast RECRUIT message.', target_address)
            self.migrating = True
        except socket.error, exc:
            logging.error("Could not send MIGRATE to node %s. Error: %s", target_address, exc)
            self.migrating = False
        return


    def poll_for_num_loyal_followers(self, neighbor_address, cluster_id):
        logging.debug("POLLING the number of loyal followers of node %s", neighbor_address)
        poll_messsage = ';'.join([str(ACE_MSG_POLL), cluster_id])
        data_arr = self.send_message(neighbor_address, poll_messsage)
        neighbohr_cluster_id = str(data_arr[0])
        neighbohr_loyal_followers = int(data_arr[1])
        logging.debug('POLL: Host %s has %s loyal folloers with id %s', neighbor_address,
                      data_arr, cluster_id)
        return neighbohr_loyal_followers, neighbohr_cluster_id


    def count_loyal_followers(self, cluster_id=''):
        # clear the list of loyal followers
        self.loyal_followers_list.clear()
        logging.debug("LOYALFOLLOWERS: Counting the number of loyal followers.")
        for neighbor_address in NEIGHBORS_MAP[self.my_ip]:
            message_to_send = str(ACE_MSG_GETSTATUS)
            # The GETSTATUS will always return a 3 elements array
            data_array = self.send_message(neighbor_address, message_to_send)
            logging.debug('LOYALFOLLOWERS: Received from host %s: %s', neighbor_address, data_array)
            neighbor_state = int(data_array[0])
            neighbor_chs = int(data_array[1])
            neighbor_ch_id = str(data_array[2])
            if neighbor_state == ACE_STATE_UNCLUSTERED:
                self.loyal_followers_list.add(neighbor_address)
            if neighbor_state == ACE_STATE_CLUSTERED and neighbor_chs == 1:
                if cluster_id != '':
                    self.loyal_followers_list.add(neighbor_address)
                elif cluster_id == neighbor_ch_id:
                    self.loyal_followers_list.add(neighbor_address)
        return len(self.loyal_followers_list)


    def locally_broadcast(self, ace_msg, node_id, cluster_id):
        for neighbor_address in NEIGHBORS_MAP[self.my_ip]:
            logging.debug("Sending RECRUIT message to node: %s", neighbor_address)
            recruit_message = ';'.join([str(ace_msg), node_id, cluster_id])
            self.send_message_noans(neighbor_address, recruit_message)


    def send_message(self, dst_address, message_str):
        logging.debug("send_message: node %s message %s", dst_address, message_str)
        response_arr = []
        for attemp in range(TCP_MAX_ATTEMPS):
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.settimeout(TCP_TIMEOUT)
            try:
                send_socket.connect((dst_address, TCP_SERVER_PORT))
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
        logging.debug("send_message_noans: node %s message %s", dst_address, message_str)
        for attemp in range(TCP_MAX_ATTEMPS):
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.settimeout(TCP_TIMEOUT)
            try:
                send_socket.connect((dst_address, TCP_SERVER_PORT))
                send_socket.send(message_str)
                send_socket.close()
            except socket.timeout:
                logging.error("send_message: Socket timeout error. Attemp %s", attemp)
                time.sleep(0.5)
            except socket.error, exc:
                logging.critical("send_message_noans: error sending message to node %s. Exception: %s",
                                 dst_address, exc)
                raise
            else:
                break
        return


    def handle_client_connection(self):
        logging.debug("CONNHANDLER: Handling client connections...")
        logging.debug("CONNHANDLER: Binding on IP: %s Port: %s.", self.my_ip, TCP_SERVER_PORT)
        r_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        r_socket.bind((self.my_ip, TCP_SERVER_PORT))
        r_socket.listen(10)
        while True:
            (client_sock, client_address) = r_socket.accept()
            logging.debug("CONNHANDLER: Connection accepted from : %s", client_address)
            request = client_sock.recv(TCP_BUFFER_SIZE)
            ace_msg = int(request.split(';')[0])
            logging.debug("CONNHANDLER: Receiving message: %s from host %s",
                          ace_msg, client_address[0])
            if ace_msg == ACE_MSG_GETSTATUS:
                logging.debug("CONNHANDLER: Receiving a GETSTATUS message.")
                # The response should include number of CHs that node is following
                r_state = str(self.my_state)
                r_number_of_chs = "0"
                r_id_of_ch = ""
                if self.my_state == ACE_STATE_CLUSTERED:
                    r_number_of_chs = str(len(self.cluster_head_list))
                    # If the node is following only a single ch, it should include the ch-id
                    # in the response
                    if (len(self.cluster_head_list)) == 1:
                        r_id_of_ch = str(self.cluster_head_list[0])
                if self.my_state == ACE_STATE_CLUSTER_HEAD:
                    r_state = str(self.my_state)
                    # r_number_of_chs = '0'
                    r_id_of_ch = self.my_cluster_id
                response_str = ';'.join([r_state, r_number_of_chs, r_id_of_ch])
                logging.debug("CONNHANDLER: Sending message %s to node %s", response_str,
                              client_address[0])
                client_sock.send(response_str)
            if ace_msg == ACE_MSG_RECRUIT:
                logging.debug("CONNHANDLER: Receiving a RECRUIT message.")
                if self.my_state == ACE_STATE_CLUSTER_HEAD:
                    logging.info("CONNHANDLER: I am a CH. I will not follow %s",
                                self.cluster_to_follow)
                else:
                    self.my_state = ACE_STATE_CLUSTERED
                    new_ch_ip = request.split(';')[1]
                    new_ch_id = request.split(';')[2]
                    self.cluster_to_follow = new_ch_ip
                    self.cluster_head_list.append(new_ch_ip)
                    logging.info("CONNHANDLER: OK! I am a follower of the CH %s",
                                self.cluster_to_follow)
            if ace_msg == ACE_MSG_POLL:
                logging.debug("CONNHANDLER: Receiving a POLL message.")
                ch_to_poll = request.split(';')[1]
                num_loyal_followers = self.count_loyal_followers(ch_to_poll)
                r_my_cluster_id = str(self.my_cluster_id)
                r_num_loyal_followers = str(num_loyal_followers)
                response_str = ';'.join([r_my_cluster_id, r_num_loyal_followers])
                client_sock.send(response_str)
                logging.debug("CONNHANDLER: POLL Done! The answer was sent.")
            if ace_msg == ACE_MSG_PROMOTE:
                cluster_id = request.split(';')[1]
                logging.debug("CONNHANDLER: Receiving a PROMOTE message.")
                self.locally_broadcast(ACE_MSG_RECRUIT, self.my_ip, cluster_id)
                self.send_promote_done(client_address[0])
            if ace_msg == ACE_MSG_PROMOTE_DONE:
                logging.debug("CONNHANDLER: Receiving a PROMOTE_DONE message.")
                self.migrating = False
            if ace_msg == ACE_MSG_ABDICATE:
                logging.debug("CONNHANDLER: Receiving a ABDICATE message.")
            client_sock.close()


    def __str__(self):
        return "Node <iii> state: " + self.my_state + "\n"


    def print_node_info(self, fmin=0):
        print "----------------------------------"
        print " Node Info:"
        print "  - IP: %s" % self.my_ip
        print "  - State: %s" % ACE_STATE_STR[self.my_state]
        print "  - Time running ACE: %.3f" % (time.time() - self.start_time)
        print "  - CH id: %s" % self.my_cluster_id
        if fmin != 0:
            print "  - F_min: %f" % fmin
        self.print_chs()
        self.print_loyal_followers()

    
    def print_chs(self):
        print "+--------------------------------+"
        print "|       Cluster Heads table      |"
        print "+--------------------------------+"
        for ch_id in self.cluster_head_list:
            print "| %-30s |" % ch_id
        print "+--------------------------------+"
        print ""


    def print_loyal_followers(self):
        print "+--------------------------------+"
        print "|     Loyal Followers table      |"
        print "+--------------------------------+"
        for followers in self.loyal_followers_list:
            print "| %-30s |" % followers
        print "+--------------------------------+"
        print ""


def main(host_ip):
    # check the parameter format. It should be an Ip ADDRESS
    if host_ip not in NEIGHBORS_MAP:
        raise Exception("Wrong host IP address.")
    ## Setting up the log system
    # log_format = "%(asctime)s: %(funcName)20s() - %(lineno)s: %(message)s"
    log_format = "%(asctime)s,%(msecs)03d:L%(lineno)4s: %(message)s"
    log_level = logging.DEBUG
    logging.basicConfig(level=log_level, 
                        format=log_format,
                        datefmt='%H:%M:%S',)
    simple_node = SimpleNode(host_ip)


def get_args(args, arg_key=''):
    return args[args.index(arg_key) + 1]


if __name__ == '__main__':
    HOST_IP = str(sys.argv[1])
    main(HOST_IP)
    raw_input("Press Enter to continue...")

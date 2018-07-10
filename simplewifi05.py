#!/usr/bin/python

import os
import sys
import time
from mininet.node import Controller
from mininet.log import setLogLevel, info
from mininet.term import makeTerm
from mininet.wifi.node import OVSKernelAP
from mininet.wifi.cli import CLI_wifi
from mininet.wifi.net import Mininet_wifi


def topology(nodes, rep):
    "Create a network."
    net = Mininet_wifi(controller=Controller, accessPoint=OVSKernelAP)

    info("*** Creating nodes\n")
    sta1 = net.addStation('sta1')
    sta2 = net.addStation('sta2')
    sta3 = net.addStation('sta3')
    sta4 = net.addStation('sta4')
    sta5 = net.addStation('sta5')

    h1 = net.addHost('h1')
    h2 = net.addHost('h2')

    ap1 = net.addAccessPoint('ap1', ssid="simplewifi", mode="g", channel="5")
    c0 = net.addController('c0', controller=Controller, ip='127.0.0.1',
                           port=6633)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Associating Stations\n")
    net.addLink(sta1, ap1)
    net.addLink(sta2, ap1)
    net.addLink(sta3, ap1)
    net.addLink(sta4, ap1)
    net.addLink(sta5, ap1)

    net.addLink(h1, ap1)
    net.addLink(h2, ap1)

    info("*** Starting network\n")
    net.build()
    c0.start()
    ap1.start([c0])

    info("*** Ping All\n")
    net.pingAll()

    h1.cmd('sudo iperf -s -u -i 1 -t 30 > iperf_s_n' + nodes + '_r' + rep + ' &')
    h2.sendCmd('iperf -u -c ' + h1.IP() + ' -b 10M -i 1 -t 30 > iperf_c_n'+ nodes +'_r' + rep)
    # removing the SDN Controller
    ap1.cmd("ovs-vsctl --db=unix:/var/run/openvswitch/db.sock del-controller ap1")

    makeTerm( sta1, cmd="python /media/sf_shared/node.py 10.0.0.1 -nodes 5 -rep 1; sleep 2" )
    makeTerm( sta2, cmd="python /media/sf_shared/node.py 10.0.0.2 -nodes 5 -rep 1; sleep 2" )
    makeTerm( sta3, cmd="python /media/sf_shared/node.py 10.0.0.3 -nodes 5 -rep 1; sleep 2" )
    makeTerm( sta4, cmd="python /media/sf_shared/node.py 10.0.0.4 -nodes 5 -rep 1; sleep 2" )
    makeTerm( sta5, cmd="python /media/sf_shared/node.py 10.0.0.5 -nodes 5 -rep 1; sleep 2" )

    info("*** Waiting for iperf to terminate.\n")
    results = {}
    results[h2] = h2.waitOutput()
    h1.cmd('kill $!')

    # info("*** Running CLI\n")
    # CLI_wifi(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    p_nodes = str(sys.argv[1].zfill(2))
    p_rep = str(sys.argv[3].zfill(2))
    setLogLevel('info')
    topology(p_nodes, p_rep)

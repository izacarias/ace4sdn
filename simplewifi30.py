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
    sta6 = net.addStation('sta6')
    sta7 = net.addStation('sta7')
    sta8 = net.addStation('sta8')
    sta9 = net.addStation('sta9')
    sta10 = net.addStation('sta10')
    sta11 = net.addStation('sta11')
    sta12 = net.addStation('sta12')
    sta13 = net.addStation('sta13')
    sta14 = net.addStation('sta14')
    sta15 = net.addStation('sta15')
    sta16 = net.addStation('sta16')
    sta17 = net.addStation('sta17')
    sta18 = net.addStation('sta18')
    sta19 = net.addStation('sta19')
    sta20 = net.addStation('sta20')
    sta21 = net.addStation('sta21')
    sta22 = net.addStation('sta22')
    sta23 = net.addStation('sta23')
    sta24 = net.addStation('sta24')
    sta25 = net.addStation('sta25')
    sta26 = net.addStation('sta26')
    sta27 = net.addStation('sta27')
    sta28 = net.addStation('sta28')
    sta29 = net.addStation('sta29')
    sta30 = net.addStation('sta30')

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
    net.addLink(sta6, ap1)
    net.addLink(sta7, ap1)
    net.addLink(sta8, ap1)
    net.addLink(sta9, ap1)
    net.addLink(sta10, ap1)
    net.addLink(sta11, ap1)
    net.addLink(sta12, ap1)
    net.addLink(sta13, ap1)
    net.addLink(sta14, ap1)
    net.addLink(sta15, ap1)
    net.addLink(sta16, ap1)
    net.addLink(sta17, ap1)
    net.addLink(sta18, ap1)
    net.addLink(sta19, ap1)
    net.addLink(sta20, ap1)
    net.addLink(sta21, ap1)
    net.addLink(sta22, ap1)
    net.addLink(sta23, ap1)
    net.addLink(sta24, ap1)
    net.addLink(sta25, ap1)
    net.addLink(sta26, ap1)
    net.addLink(sta27, ap1)
    net.addLink(sta28, ap1)
    net.addLink(sta29, ap1)
    net.addLink(sta30, ap1)

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

    makeTerm( sta1, cmd="python /media/sf_shared/node.py 10.0.0.1 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta2, cmd="python /media/sf_shared/node.py 10.0.0.2 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta3, cmd="python /media/sf_shared/node.py 10.0.0.3 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta4, cmd="python /media/sf_shared/node.py 10.0.0.4 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta5, cmd="python /media/sf_shared/node.py 10.0.0.5 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta6, cmd="python /media/sf_shared/node.py 10.0.0.6 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta7, cmd="python /media/sf_shared/node.py 10.0.0.7 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta8, cmd="python /media/sf_shared/node.py 10.0.0.8 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta9, cmd="python /media/sf_shared/node.py 10.0.0.9 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta10, cmd="python /media/sf_shared/node.py 10.0.0.10 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta11, cmd="python /media/sf_shared/node.py 10.0.0.11 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta12, cmd="python /media/sf_shared/node.py 10.0.0.12 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta13, cmd="python /media/sf_shared/node.py 10.0.0.13 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta14, cmd="python /media/sf_shared/node.py 10.0.0.14 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta15, cmd="python /media/sf_shared/node.py 10.0.0.15 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta16, cmd="python /media/sf_shared/node.py 10.0.0.16 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta17, cmd="python /media/sf_shared/node.py 10.0.0.17 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta18, cmd="python /media/sf_shared/node.py 10.0.0.18 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta19, cmd="python /media/sf_shared/node.py 10.0.0.19 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta20, cmd="python /media/sf_shared/node.py 10.0.0.20 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta21, cmd="python /media/sf_shared/node.py 10.0.0.21 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta22, cmd="python /media/sf_shared/node.py 10.0.0.22 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta23, cmd="python /media/sf_shared/node.py 10.0.0.23 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta24, cmd="python /media/sf_shared/node.py 10.0.0.24 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta25, cmd="python /media/sf_shared/node.py 10.0.0.25 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta26, cmd="python /media/sf_shared/node.py 10.0.0.26 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta27, cmd="python /media/sf_shared/node.py 10.0.0.27 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta28, cmd="python /media/sf_shared/node.py 10.0.0.28 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta29, cmd="python /media/sf_shared/node.py 10.0.0.29 -nodes 30 -rep 1;sleep 2" )
    makeTerm( sta30, cmd="python /media/sf_shared/node.py 10.0.0.30 -nodes 30 -rep 1;sleep 2" )

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

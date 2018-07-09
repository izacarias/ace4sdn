#!/usr/bin/python

'This example creates a simple network topology with 1 AP and 2 stations'

import sys
import time
from mininet.node import Controller
from mininet.log import setLogLevel, info
from mininet.term import makeTerm
from mininet.wifi.node import OVSKernelAP
from mininet.wifi.cli import CLI_wifi
from mininet.wifi.net import Mininet_wifi


def topology():
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

    ap1 = net.addAccessPoint('ap1', ssid="simplewifi", mode="g", channel="5")
    ap2 = net.addAccessPoint('ap2', ssid="simplewifi", mode="g", channel="5")
    ap3 = net.addAccessPoint('ap3', ssid="simplewifi", mode="g", channel="5")

    c0 = net.addController('c0', controller=Controller, ip='127.0.0.1',
                           port=6633)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    net.addLink(ap1, ap2)
    net.addLink(ap2, ap3)

    info("*** Associating Stations\n")
    net.addLink(sta1, ap1)
    net.addLink(sta2, ap1)
    net.addLink(sta3, ap1)
    net.addLink(sta4, ap1)
    net.addLink(sta5, ap1)
    net.addLink(sta6, ap2)
    net.addLink(sta7, ap2)
    net.addLink(sta8, ap2)
    net.addLink(sta9, ap2)
    net.addLink(sta10, ap2)
    net.addLink(sta11, ap3)
    net.addLink(sta12, ap3)
    net.addLink(sta13, ap3)
    net.addLink(sta14, ap3)
    net.addLink(sta15, ap3)

    info("*** Starting network\n")
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])

    info("*** Ping All\n")
    net.pingAll()

    time.sleep(2)

    # print "Sta1 IP: %s" % sta1.params['ip'][0].split('/')[0]
    makeTerm( sta1, cmd="python /media/sf_shared/node.py 10.0.0.1 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta2, cmd="python /media/sf_shared/node.py 10.0.0.2 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta3, cmd="python /media/sf_shared/node.py 10.0.0.3 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta4, cmd="python /media/sf_shared/node.py 10.0.0.4 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta5, cmd="python /media/sf_shared/node.py 10.0.0.5 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta6, cmd="python /media/sf_shared/node.py 10.0.0.6 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta7, cmd="python /media/sf_shared/node.py 10.0.0.7 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta8, cmd="python /media/sf_shared/node.py 10.0.0.8 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta9, cmd="python /media/sf_shared/node.py 10.0.0.9 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta10, cmd="python /media/sf_shared/node.py 10.0.0.10 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta11, cmd="python /media/sf_shared/node.py 10.0.0.11 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta12, cmd="python /media/sf_shared/node.py 10.0.0.12 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta13, cmd="python /media/sf_shared/node.py 10.0.0.13 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta14, cmd="python /media/sf_shared/node.py 10.0.0.14 -nodes 15 -rep 1;sleep 2" )
    makeTerm( sta15, cmd="python /media/sf_shared/node.py 10.0.0.15 -nodes 15 -rep 1;sleep 2" )

    info("*** Running CLI\n")
    # CLI_wifi(net)
    time.sleep(17)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()

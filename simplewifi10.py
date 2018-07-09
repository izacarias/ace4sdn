#!/usr/bin/python

'This example creates a simple network topology with 1 AP and 2 stations'

import sys
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

    info("*** Starting network\n")
    net.build()
    c0.start()
    ap1.start([c0])

    info("*** Ping All\n")
    net.pingAll()

    # print "Sta1 IP: %s" % sta1.params['ip'][0].split('/')[0]
    makeTerm( sta1, cmd="python /media/sf_shared/node.py 10.0.0.1 -nodes 10 -rep 1;read" )
    makeTerm( sta2, cmd="python /media/sf_shared/node.py 10.0.0.2 -nodes 10 -rep 1;read" )
    makeTerm( sta3, cmd="python /media/sf_shared/node.py 10.0.0.3 -nodes 10 -rep 1;read" )
    makeTerm( sta4, cmd="python /media/sf_shared/node.py 10.0.0.4 -nodes 10 -rep 1;read" )
    makeTerm( sta5, cmd="python /media/sf_shared/node.py 10.0.0.5 -nodes 10 -rep 1;read" )
    makeTerm( sta6, cmd="python /media/sf_shared/node.py 10.0.0.6 -nodes 10 -rep 1;read" )
    makeTerm( sta7, cmd="python /media/sf_shared/node.py 10.0.0.7 -nodes 10 -rep 1;read" )
    makeTerm( sta8, cmd="python /media/sf_shared/node.py 10.0.0.8 -nodes 10 -rep 1;read" )
    makeTerm( sta9, cmd="python /media/sf_shared/node.py 10.0.0.9 -nodes 10 -rep 1;read" )
    makeTerm( sta10, cmd="python /media/sf_shared/node.py 10.0.0.10 -nodes 10 -rep 1;read" )

    info("*** Running CLI\n")
    CLI_wifi(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()

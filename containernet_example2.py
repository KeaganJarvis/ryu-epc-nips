#!/usr/bin/python
"""
This is the most simple example to showcase Containernet.
"""
from mininet.net import Containernet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

net = Containernet(controller=RemoteController,autoSetMacs=False)
info('*** Adding controller\n')
net.addController('c0')
info('*** Adding docker containers\n')
hss = net.addDocker('hss', ip='10.0.0.251', mac='11:11:11:11:11:11', dimage="ubuntu:trusty") #33:33:00:00:00:fb
mme = net.addDocker('mme', ip='10.0.0.252', mac='22:22:22:22:22:22', dimage="ubuntu:trusty") #fe:e4:1c:1b:df:78
info('*** Adding switches\n')
s1 = net.addSwitch('s1')
s2 = net.addSwitch('s2')
info('*** Creating links\n')
net.addLink(hss, s1)
net.addLink(s1, s2, cls=TCLink, delay='100ms', bw=1)
net.addLink(s2, mme)
info('*** Starting network\n')
net.start()
info('*** Testing connectivity\n')
net.ping([hss, mme])
info('*** Running CLI\n')
CLI(net)
info('*** Stopping network')
net.stop()


#!/usr/bin/python
"""
This is the most simple example to showcase Containernet.
"""
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

net = Mininet(controller=RemoteController)
info('*** Adding controller\n')
net.addController('c1')
info('*** Adding docker containers\n')
hss = net.addHost('hss', ip='10.0.0.252', mac='42:42:42:42:42:42') #33:33:00:00:00:fb
mme = net.addHost('mme', ip='10.0.0.252', mac='13:13:13:13:13:13') #fe:e4:1c:1b:df:78 ca:79:7e:42:c3:2c
info('*** Adding switches\n')
s5 = net.addSwitch('s5')
# s6 = net.addSwitch('s6')
info('*** Creating links\n')
net.addLink(hss, s5)
# net.addLink(s5, s6, cls=TCLink, delay='10ms', bw=1)
net.addLink(s5, mme)
info('*** Starting network\n')
net.start()
info('*** Testing connectivity\n')
net.ping([hss, mme])
info('*** Running CLI\n')
CLI(net)
info('*** Stopping network')
net.stop()


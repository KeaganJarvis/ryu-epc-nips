#!/usr/bin/python
"""
This is the EPC implementation inside container net
"""
from mininet.net import Containernet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

net = Containernet(controller=RemoteController)
info('*** Adding controller\n')
c0 = net.addController('c0', ip='172.17.0.1', port=6633)
info('*** Adding docker containers\n')
hss = net.addDocker('hss', ip='10.0.0.251', dimage="ssh:latest")
comp = net.addDocker('comp', ip='10.0.0.252', dimage="ssh:latest")
mme = net.addDocker('mme', ip='10.0.0.253', dimage="ssh:latest")
spgw = net.addDocker('spgw', ip='10.0.0.254', dimage="ssh:latest")

info('*** Adding switches\n')
s1 = net.addSwitch('s1')
# s2 = net.addSwitch('s2')
info('*** Creating links\n')
net.addLink(hss, s1)
# net.addLink(s1, s2, cls=TCLink, delay='100ms', bw=1)
net.addLink(s1, comp)
net.addLink(s1, mme)
net.addLink(s1, spgw)
info('*** Starting network\n')
net.start()
info('*** Testing connectivity\n')
net.ping([hss, mme])
net.ping([spgw, mme])
net.ping([comp, mme])
info('*** Running CLI\n')
CLI(net)
info('*** Stopping network')
net.stop()


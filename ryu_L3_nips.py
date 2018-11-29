# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
# from mininet.net import Containernet
# from mininet.node import RemoteController
# from test import a


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        # import pudb; pudb.set_trace()

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)


    def malicious_flow(self, src, dst):
        if src == '10.0.0.251' and dst == '10.0.0.252':
            return True
        else:
            return False

    def deploy_decoy (self):
        import docker
        client = docker.from_env()
        print ('Deploying decoy')

        try:
            # client.containers.get('decoy-hss')
            client.containers.run("ssh:latest", detach=True, name='decoy-hss')
        except docker.errors.APIError as exists:
            print ("decoy exists")


    def alert(self):
        from slackclient import SlackClient
        import os
        # instantiate Slack client
        slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
        # starterbot's user ID in Slack: value is assigned after the bot starts up
        alertbot_id = None

        if slack_client.rtm_connect(with_team_state=False):
            print("Alert Bot connected and running!")
            # Read bot's user ID by calling Web API method `auth.test`
            alertbot_id = slack_client.api_call("auth.test")["user_id"]
            slack_client.api_call(
                "chat.postMessage",
                channel='nips',
                text='ALERT, malicious flow detected in EPC'
            )
        else:
            print("Connection failed. Exception traceback printed above.")


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src


        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        #self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time

        # if out_port != ofproto.OFPP_FLOOD:


            # check IP Protocol and create a match for IP
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ip = pkt.get_protocol(ipv4.ipv4)
            srcip = ip.src
            dstip = ip.dst

            #check if flow is malicious
            if self.malicious_flow(srcip, dstip):
                print 'malicious flow detected'
                self.alert()
                #deploy decoy inside mn
                self.deploy_decoy()
                #redirect flow to decoy
                print ("redirecting the flow to the deployed decoy")
                #this can be done by changing the dstip obj to the ip of the decoy

            else:
                print 'flow is not malicious'
                #continue as is installing the flow rule

            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                    ipv4_src=srcip,
                                    ipv4_dst=dstip
                                    )
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)


############################################################################################################
#NB DONT FOGET THE MININET FOLDER COPIED INTO /home/keagan/.local/lib/python2.7/site-packages/
############################################################################################################

# """
# This is the EPC implementation inside container net
# """
# from mininet.net import Containernet
# from mininet.node import RemoteController
# # from mininet.cli import CLI
# from mininet.link import TCLink
# from mininet.log import info, setLogLevel
# setLogLevel('info')

# a = 3
# net = Containernet(controller=RemoteController,autoSetMacs=False)
# info('*** Adding controller\n')
# net.addController('c0')
# info('*** Adding docker containers\n')
# hss = net.addDocker('hss', ip='10.0.0.251', dimage="ssh:latest") #33:33:00:00:00:fb
# mme = net.addDocker('mme', ip='10.0.0.252', dimage="ssh:latest") #fe:e4:1c:1b:df:78
# info('*** Adding switches\n')
# s1 = net.addSwitch('s1')
# #s2 = net.addSwitch('s2')
# info('*** Creating links\n')
# net.addLink(hss, s1)
# #net.addLink(s1, s2, cls=TCLink, delay='100ms', bw=1)
# net.addLink(s1, mme)
# info('*** Starting network\n')
# net.start()
# info('*** Testing connectivity\n')
# #net.ping([hss, mme])
# info('*** Running CLI\n')
# # CLI(net)
# info('*** Stopping network')
# net.stop()

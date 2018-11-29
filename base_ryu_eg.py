from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER

class L2Forwarding(app_manager.RyuApp):
    def __init__(self, *args, **kwargs):
        super(L2Forwarding, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg               # Object representing a packet_in data structure.
        datapath = msg.datapath    # Switch Datapath ID
        ofproto = datapath.ofproto # OpenFlow Protocol version the entities negotiated. In our case OF1.3
        from ryu.lib.packet import packet
        from ryu.lib.packet import ethernet
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        dst = eth.dst
        src = eth.src
        #out = ofp_parser.OFPPacketOut(datapath=dp,in_port=msg.in_port,actions=actions)#Generate the message
        #dp.send_msg(out) #Send the message to the switch
        print dst
        print src
##Network protocol
#
# Implement network protocols at the local host
#
# @author ykk
# @date May 2011
#
import yapc.interface as yapc
import yapc.pyopenflow as pyof
import yapc.log.output as output
import yapc.events.openflow as ofevents
import yapc.util.memcacheutil as mcutil
import yapc.util.parse as pu
import dpkt

class dhcp(yapc.component):
    """Component that sends and interprets DHCP packets from interfaces on switch

    Record of IP address and gateway saved in memcache
    
    @author ykk
    @date May 2011
    """
    #Key prefix for datapath_id and port
    DP_PORT_KEY_PREFIX = "dhcp_dp_port_"
    def __init__(self, server, ofconn):
        """Initialize

        @param server yapc core server/scheduler
        @param ofconn OpenFlow connections
        """
        #Start memcache
        mcutil.get_client()
        ##OpenFlow connections
        self.ofconnections = ofconn
        
        server.register_event_handler(ofevents.pktin.name,
                                      self)

    def dhclient(self, dpid, port, mac):
        """Invoke dhclient on dpid and port given

        @param dpid datapath
        @param port port
        @param mac mac addr of port
        """
        #Form DHCP request
        dhreq = dpkt.dhcp.DHCP()
        setattr(dhreq, "chaddr", mac)
        opts = []
        opts.append((dpkt.dhcp.DHCP_OPT_MSGTYPE, chr(dpkt.dhcp.DHCPDISCOVER)))
        opts.append((dpkt.dhcp.DHCP_OPT_HOSTNAME, "coin"))
        opts.append((dpkt.dhcp.DHCP_OPT_PARAM_REQ, chr(1)+chr(28)+chr(2)+chr(3)+chr(15)+\
                         chr(6)+chr(119)+chr(12)+chr(44)+chr(47)+chr(26)+chr(121)+chr(42)))
        setattr(dhreq, "opts", opts)
        dreq = dhreq.pack()+chr(0)*43

        #Form UDP packet
        udppkt = dpkt.udp.UDP()
        setattr(udppkt, "sport", 68)
        setattr(udppkt, "dport", 67)
        setattr(udppkt, "ulen", len(dreq))
        setattr(udppkt, "data", dreq)
        
        #Form IP packet
        ippkt = dpkt.ip.IP()
        setattr(ippkt, "dst",  pu.array2byte_str([0xff, 0xff, 0xff, 0xff]))
        setattr(ippkt, "len", len(dreq)+20)
        setattr(ippkt, "p", dpkt.ip.IP_PROTO_UDP)
        setattr(ippkt, "data", udppkt)

        #Form Ethernet packet
        ethpkt = dpkt.ethernet.Ethernet()
        setattr(ethpkt, "src", mac)
        setattr(ethpkt, "dst", pu.array2byte_str([0xff, 0xff, 0xff, 0xff, 0xff, 0xff]))
        setattr(ethpkt, "data", ippkt)

        output.dbg(`ethpkt`,
                   self.__class__.__name__)

        #Form packet out
        opo = pyof.ofp_packet_out()
        oao = pyof.ofp_action_output()
        oao.port = port
        opo.in_port = pyof.OFPP_NONE
        opo.actions_len = pyof.OFP_ACTION_OUTPUT_BYTES
        opo.actions.append(oao)

        self.ofconnections.get_conn(dpid).send(opo.pack()+ethpkt.pack())

        output.dbg("dhclient on %x" % dpid + ":"+str(port),
                   self.__class__.__name__)

    def get_key(dpid, port):
        """Get key for IP address and gateway IP

        @param dpid datapath id of switch
        @param port port number of interface
        """
        return dhcp.DP_PORT_KEY_PREFIX+"%x_" % dpid+str(port).strip()
    get_key = yapc.static_callable(get_key)

    def processevent(self, event):
        """Process OpenFlow messages

        @param event event to handle
        @return True for everything other than DHCP reply
        """
        if (isinstance(event, ofevents.pktin)):
            if (event.match.dl_type == dpkt.ethernet.ETH_TYPE_IP and
                event.match.nw_proto == dpkt.ip.IP_PROTO_UDP and
                event.match.tp_dst == 68):
                output.dbg("Got packet DHCP reply packet:\n\t"+`event.dpkt`,
                           self.__class__.__name__)
        
        return True


##Definition of flows
#
# Some generic definition of flows
#
# @author ykk
# @date Feb 2011
#
import dpkt
import yapc.openflowutil as ofutil
import yapc.pyopenflow as pyof

UDP_BOOTPS = 67
UDP_BOOTPC = 68
UDP_SUNRPC = 111
UDP_NETBIOS = 137
UDP_NETBIOS_DGM = 138
UDP_MS_LICENSE = 2223
UDP_MDNS = 5353

class flow_entry:
    """Class to provide some pre-formed flow entry

    @author ykk
    @date Feb 2011
    """
    DROP = 0
    GET = 1
    FLOOD = 2
    def __init__(self, action):
        """Initialize
        """
        self.fm = pyof.ofp_flow_mod()

        oao = pyof.ofp_action_output()
        oao.max_len = pyof.OFP_DEFAULT_MISS_SEND_LEN
        if (action == flow_entry.GET):
            oao.port = pyof.OFPP_CONTROLLER
        elif (action == flow_entry.FLOOD):
            oao.port = pyof.OFPP_FLOOD

        if (action != flow_entry.DROP):
            self.fm.actions.append(oao)

    def get_flow_mod(self):
        """Function to return flow_entry in terms of flow mod.

        @return ofp_flow_mod
        """
        self.fm.header.xid = ofutil.get_xid()
        return self.fm

class all_entry(flow_entry):
    """Flow entry for all packets

    Uses as a low priority default

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 action,
                 priority = ofutil.PRIORITY['LOWEST'],
                 idle_timeout = pyof.OFP_FLOW_PERMANENT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        flow_entry.__init__(self, action)

        self.fm.match.wildcards = pyof.OFPFW_ALL
        self.fm.command = pyof.OFPFC_ADD
        self.fm.priority = priority
        self.fm.idle_timeout = idle_timeout
        self.fm.hard_timeout = hard_timeout

class ethertype_entry(flow_entry):
    """Flow entry that is based Ethertype

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 action,
                 ethertype,
                 priority = ofutil.PRIORITY['LOW'],
                 idle_timeout = pyof.OFP_FLOW_PERMANENT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        flow_entry.__init__(self, action)

        self.fm.match.wildcards = pyof.OFPFW_ALL - pyof.OFPFW_DL_TYPE
        self.fm.match.dl_type = ethertype
        self.fm.command = pyof.OFPFC_ADD
        self.fm.priority = priority
        self.fm.idle_timeout = idle_timeout
        self.fm.hard_timeout = hard_timeout

class arp_entry(ethertype_entry):
    """Flow entry for ARP packets

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 action,
                 priority = ofutil.PRIORITY['LOW'],
                 idle_timeout = pyof.OFP_FLOW_PERMANENT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        ethertype_entry.__init__(self, action, dpkt.ethernet.ETH_TYPE_ARP,
                                 priority, idle_timeout, hard_timeout)

class ip_proto_entry(flow_entry):
    """Flow entry that is based IP Protocol number

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 action,
                 ip_proto,
                 priority = ofutil.PRIORITY['LOW'],
                 idle_timeout = pyof.OFP_FLOW_PERMANENT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        flow_entry.__init__(self,action)
       
        self.fm.match.wildcards = pyof.OFPFW_ALL-\
            pyof.OFPFW_DL_TYPE - pyof.OFPFW_NW_PROTO
        self.fm.match.dl_type = dpkt.ethernet.ETH_TYPE_IP
        self.fm.match.nw_proto = ip_proto
        self.fm.command = pyof.OFPFC_ADD
        self.fm.priority = priority
        self.fm.idle_timeout = idle_timeout
        self.fm.hard_timeout = hard_timeout


class icmp_entry(ip_proto_entry):
    """Flow entry to handle ICMP packets

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 action,
                 priority = ofutil.PRIORITY['LOW'],
                 idle_timeout = pyof.OFP_FLOW_PERMANENT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        ip_proto_entry.__init__(self,action, dpkt.ip.IP_PROTO_ICMP,
                                priority, idle_timeout, hard_timeout)
       
class igmp_entry(ip_proto_entry):
    """Flow entry to handle IGMP

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 action,
                 priority = ofutil.PRIORITY['LOW'],
                 idle_timeout = pyof.OFP_FLOW_PERMANENT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        ip_proto_entry.__init__(self,action, dpkt.ip.IP_PROTO_IGMP,
                                priority, idle_timeout, hard_timeout)

class udp_entry(ip_proto_entry):
    """Flow entry for UDP packets

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 action, 
                 portno = None,
                 priority = ofutil.PRIORITY['LOW'],
                 idle_timeout = pyof.OFP_FLOW_PERMANENT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        ip_proto_entry.__init__(self,action, dpkt.ip.IP_PROTO_UDP,
                                priority, idle_timeout, hard_timeout)

        if (portno != None):
            self.fm.match.wildcards -= pyof.OFPFW_TP_DST
            self.fm.match.tp_dst = portno

class tcp_entry(ip_proto_entry):
    """Flow entry for TCP packets

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 action,
                 portno = None,
                 priority = ofutil.PRIORITY['LOW'],
                 idle_timeout = pyof.OFP_FLOW_PERMANENT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        flow_entry.__init__(self, action)

        ip_proto_entry.__init__(self,action, dpkt.ip.IP_PROTO_TCP,
                                priority, idle_timeout, hard_timeout)       

        if (portno != None):
            self.fm.match.wildcards -= pyof.OFPFW_TP_DST
            self.fm.match.tp_dst = portno

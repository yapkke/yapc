##Definition of flows
#
# Some generic definition of flows
#
# @author ykk
# @date Feb 2011
#
import dpkt
import yapc.util.openflow as ofutil
import yapc.pyopenflow as pyof
import yapc.output as output

UDP_BOOTPS = 67
UDP_BOOTPC = 68
UDP_SUNRPC = 111
UDP_NETBIOS = 137
UDP_NETBIOS_DGM = 138
UDP_MS_LICENSE = 2223
UDP_MDNS = 5353

##Buffer id of unbuffered packet
UNBUFFERED_ID = 4294967295
##Default timeout value
DEFAULT_TIMEOUT = 5

class actions:
    """Class to provide management of ofp_actions list
    
    @author ykk
    @date Feb 2011
    """
    def __init__(self, buffer_id=UNBUFFERED_ID):
        """Initialize
        """
        ##List of actions
        self.actions = []
        ##Buffer id
        self.buffer_id = buffer_id

    def add(self, action):
        """Add more actions to list
        """
        self.actions.append(action)

    def add_output(self, port=pyof.OFPP_CONTROLLER):
        """Add output action to list
        """
        oao = pyof.ofp_action_output()
        oao.max_len = pyof.OFP_DEFAULT_MISS_SEND_LEN
        oao.port = port
        self.add(oao)

    def add_nw_rewrite(self, rewrite_src, addr):
        """Add rewrite for IP destination

        @param rewrite_src boolean for indicated rewrite src or dst
        """
        oanw = pyof.ofp_action_nw_addr()
        if (rewrite_src):
            oanw.type = pyof.OFPAT_SET_NW_SRC
        else:
            oanw.type = pyof.OFPAT_SET_NW_DST
        oanw.nw_addr = addr
        self.add(oanw)

    def set_buffer(self, buffer_id):
        """Set buffer id
        """
        self.buffer_id = buffer_id

class flow_entry(actions):
    """Class to provide some pre-formed flow entry

    @author ykk
    @date Feb 2011
    """
    NONE = 0
    DROP = 0
    GET = 1
    FLOOD = 2
    def __init__(self, action=NONE):
        """Initialize
        """
        actions.__init__(self)
        ##Match
        self.match = pyof.ofp_match()
        ##Idle timeout
        self.idle_timeout = DEFAULT_TIMEOUT
        ##Hard timeout
        self.hard_timeout = pyof.OFP_FLOW_PERMANENT
        ##Priority
        self.priority = pyof.OFP_DEFAULT_PRIORITY
        ##Out port
        self.out_port = pyof.OFPP_NONE
        ##Flags
        self.flags = 0

        if (action == flow_entry.GET):
            self.add_output(pyof.OFPP_CONTROLLER)
        elif (action == flow_entry.FLOOD):
            self.add_output(pyof.OFPP_FLOOD)

    def reverse(self, in_port):
        """Compute the reverse flow

        Heavily wildcarded except for addresses and ports
        
        @param in_port in port of the reverse flow
        @return reverse flow
        """
        fe = flow_entry()
        fe.match.wildcards = pyof.OFPFW_ALL - pyof.OFPFW_IN_PORT - \
            pyof.OFPFW_DL_SRC - pyof.OFPFW_DL_DST - \
            pyof.OFPFW_NW_SRC_ALL - pyof.OFPFW_NW_DST_ALL - \
            pyof.OFPFW_TP_SRC - pyof.OFPFW_TP_DST
        fe.match.in_port = in_port
        fe.match.dl_src = self.match.dl_dst
        fe.match.dl_dst = self.match.dl_src
        fe.match.nw_src = self.match.nw_dst
        fe.match.nw_dst = self.match.nw_src
        fe.match.tp_src = self.match.tp_dst
        fe.match.tp_dst = self.match.tp_src

        fe.idle_timeout = self.idle_timeout
        fe.hard_timeout = self.hard_timeout
        fe.priority = self.priority
        fe.out_port = self.out_port
        fe.flags = self.flags
        return fe

    def is_reverse(self, flow):
        """Check if flow is reverse flow

        Check wildcards and 
        dl_src/dl_dst, nw_src/nw_dst and tp_src/tp_dst

        @param flow reference to other flow
        @return reverse flow or not
        """
        if (not self.__reverse_flow(self.match.wildcards & pyof.OFPFW_DL_SRC,
                                    self.match.wildcards & pyof.OFPFW_DL_DST,
                                    self.match.dl_src,
                                    self.match.dl_dst,
                                    flow.match.wildcards & pyof.OFPFW_DL_SRC,
                                    flow.match.wildcards & pyof.OFPFW_DL_DST,
                                    flow.match.dl_src,
                                    flow.match.dl_dst)):
            return False

        if (not self.__reverse_flow(self.match.wildcards & pyof.OFPFW_NW_SRC_ALL,
                                    self.match.wildcards & pyof.OFPFW_NW_DST_ALL,
                                    self.match.nw_src,
                                    self.match.nw_dst,
                                    flow.match.wildcards & pyof.OFPFW_NW_SRC_ALL,
                                    flow.match.wildcards & pyof.OFPFW_NW_DST_ALL,
                                    flow.match.nw_src,
                                    flow.match.nw_dst)):
            return False

        if (not self.__reverse_flow(self.match.wildcards & pyof.OFPFW_TP_SRC,
                                    self.match.wildcards & pyof.OFPFW_TP_DST,
                                    self.match.tp_src,
                                    self.match.tp_dst,
                                    flow.match.wildcards & pyof.OFPFW_TP_SRC,
                                    flow.match.wildcards & pyof.OFPFW_TP_DST,
                                    flow.match.tp_src,
                                    flow.match.tp_dst)):
            return False

        return True


    def __reverse_flow(self, wild_src, wild_dst, src_val, dst_val,
                       other_wild_src, other_wild_dst, other_src_val, other_dst_val):
        """Check if reverse flow for specific layer
        """
        if (wild_src != other_wild_dst):
            return False
        elif (wild_src == 0 and
              src_val != other_dst_val):
                return False
        
        if (wild_dst != other_wild_src):
            return False
        elif (wild_src == 0 and
              dst_val != other_src_val):
                return False

        return True
            

    def set_priority(self, priority):
        """Set priority of flow entry

        Priority can be expressed as number or 
        one of the following string expressed in yapc.openflowutil
       
        @param priority expression of priority
        @return success
        """
        if (isinstance(priority, int)):
            self.priority = priority
        elif (priority in ofutil.PRIORITY):
            self.priority = ofutil.PRIORITY[priority]
        else:
            output.warn("Unknown expression of priority "+str(priority),
                        self.__class__.__name__)
            return False

        return True

    def get_packet_out(self, set_unbuffered=False):
        """Function to return flow_entry in terms of packet out

        @param set_unbuffered set packet out to for unbuffered packet
        @return ofp_packet_out
        """
        po = pyof.ofp_packet_out()
        if (set_unbuffered):
            po.buffer_id = UNBUFFERED_ID
        else:
            po.buffer_id = self.buffer_id
        po.in_port = self.match.in_port
        po.actions_len = 0
        for a in self.actions:
            po.actions_len += a.len
        po.actions = self.actions[:]

        return po

    def get_flow_mod(self, command=pyof.OFPFC_ADD, 
                     cookie=0):
        """Function to return flow_entry in terms of flow mod.

        @return ofp_flow_mod
        """
        fm = pyof.ofp_flow_mod()
        fm.match = self.match
        fm.cookie = cookie
        fm.command = command
        fm.idle_timeout = self.idle_timeout
        fm.hard_timeout = self.hard_timeout
        fm.priority = self.priority
        fm.buffer_id = self.buffer_id
        fm.out_port = self.out_port
        fm.flags = self.flags       
        fm.actions = self.actions[:]

        fm.header.xid = ofutil.get_xid()
        return fm

class exact_entry(flow_entry):
    """Flow entry with exact match

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 match,
                 action=flow_entry.NONE,
                 priority = ofutil.PRIORITY['DEFAULT'],
                 idle_timeout = DEFAULT_TIMEOUT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        flow_entry.__init__(self, action)

        self.match = match
        self.priority = priority
        self.idle_timeout = idle_timeout
        self.hard_timeout = hard_timeout

class all_entry(flow_entry):
    """Flow entry for all packets

    Uses as a low priority default

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 action=flow_entry.NONE,
                 priority = ofutil.PRIORITY['DEFAULT'],
                 idle_timeout = DEFAULT_TIMEOUT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        flow_entry.__init__(self, action)

        self.match.wildcards = pyof.OFPFW_ALL
        self.priority = priority
        self.idle_timeout = idle_timeout
        self.hard_timeout = hard_timeout

class ethertype_entry(flow_entry):
    """Flow entry that is based Ethertype

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 ethertype,
                 action=flow_entry.NONE,
                 priority = ofutil.PRIORITY['DEFAULT'],
                 idle_timeout = DEFAULT_TIMEOUT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        flow_entry.__init__(self, action)

        self.match.wildcards = pyof.OFPFW_ALL - pyof.OFPFW_DL_TYPE
        self.match.dl_type = ethertype
        self.priority = priority
        self.idle_timeout = idle_timeout
        self.hard_timeout = hard_timeout

class arp_entry(ethertype_entry):
    """Flow entry for ARP packets

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 action=flow_entry.NONE,
                 priority = ofutil.PRIORITY['DEFAULT'],
                 idle_timeout = DEFAULT_TIMEOUT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        ethertype_entry.__init__(self, dpkt.ethernet.ETH_TYPE_ARP, action,
                                 priority, idle_timeout, hard_timeout)

class ip_proto_entry(flow_entry):
    """Flow entry that is based IP Protocol number

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 ip_proto,
                 action=flow_entry.NONE,
                 priority = ofutil.PRIORITY['DEFAULT'],
                 idle_timeout = DEFAULT_TIMEOUT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        flow_entry.__init__(self,action)
       
        self.match.wildcards = pyof.OFPFW_ALL-\
            pyof.OFPFW_DL_TYPE - pyof.OFPFW_NW_PROTO
        self.match.dl_type = dpkt.ethernet.ETH_TYPE_IP
        self.match.nw_proto = ip_proto
        self.priority = priority
        self.idle_timeout = idle_timeout
        self.hard_timeout = hard_timeout


class icmp_entry(ip_proto_entry):
    """Flow entry to handle ICMP packets

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 action=flow_entry.NONE,
                 priority = ofutil.PRIORITY['DEFAULT'],
                 idle_timeout = DEFAULT_TIMEOUT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        ip_proto_entry.__init__(self, dpkt.ip.IP_PROTO_ICMP, action,
                                priority, idle_timeout, hard_timeout)
       
class igmp_entry(ip_proto_entry):
    """Flow entry to handle IGMP

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 action=flow_entry.NONE,
                 priority = ofutil.PRIORITY['DEFAULT'],
                 idle_timeout = DEFAULT_TIMEOUT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        ip_proto_entry.__init__(self, dpkt.ip.IP_PROTO_IGMP, action,
                                priority, idle_timeout, hard_timeout)

class udp_entry(ip_proto_entry):
    """Flow entry for UDP packets

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 portno = None,
                 action=flow_entry.NONE,
                 priority = ofutil.PRIORITY['DEFAULT'],
                 idle_timeout = DEFAULT_TIMEOUT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        ip_proto_entry.__init__(self, dpkt.ip.IP_PROTO_UDP, action,
                                priority, idle_timeout, hard_timeout)

        if (portno != None):
            self.match.wildcards -= pyof.OFPFW_TP_DST
            self.match.tp_dst = portno

class tcp_entry(ip_proto_entry):
    """Flow entry for TCP packets

    @author ykk
    @date Feb 2011
    """
    def __init__(self, 
                 portno = None,
                 action=flow_entry.NONE,
                 priority = ofutil.PRIORITY['DEFAULT'],
                 idle_timeout = DEFAULT_TIMEOUT,
                 hard_timeout = pyof.OFP_FLOW_PERMANENT):
        """Initialize
        """
        flow_entry.__init__(self, action)

        ip_proto_entry.__init__(self, dpkt.ip.IP_PROTO_TCP, action,
                                priority, idle_timeout, hard_timeout)       

        if (portno != None):
            self.match.wildcards -= pyof.OFPFW_TP_DST
            self.match.tp_dst = portno

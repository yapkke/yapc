##Definition of flows
#
# Some generic definition of flows
#
# @author ykk
# @date Feb 2011
#
import dpkt
import yapc.util.openflow as ofutil
import yapc.packet.ofaction as pktact
import yapc.pyopenflow as pyof
import yapc.log.output as output

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

    def add_output(self, port=pyof.OFPP_CONTROLLER, 
                   max_len=pyof.OFP_DEFAULT_MISS_SEND_LEN):
        """Add output action to list
        """
        oao = pyof.ofp_action_output()
        oao.max_len = max_len
        oao.port = port
        self.add(oao)

    def add_nw_rewrite(self, rewrite_src, addr):
        """Add rewrite for IP address

        @param rewrite_src boolean for indicated rewrite src or dst
        @param addr address to rewrite to
        """
        oanw = pyof.ofp_action_nw_addr()
        if (rewrite_src):
            oanw.type = pyof.OFPAT_SET_NW_SRC
        else:
            oanw.type = pyof.OFPAT_SET_NW_DST
        oanw.nw_addr = addr
        self.add(oanw)

    def add_dl_rewrite(self, rewrite_src, addr):
        """Add rewrite for Ethernet addr

        @param rewrite_src boolean for indicated rewrite src or dst
        @param addr address to rewrite to
        """
        oadl = pyof.ofp_action_dl_addr()
        if (rewrite_src):
            oadl.type = pyof.OFPAT_SET_DL_SRC
        else:
            oadl.type = pyof.OFPAT_SET_DL_DST
        oadl.dl_addr = addr
        self.add(oadl)

    def set_buffer(self, buffer_id):
        """Set buffer id
        """
        self.buffer_id = buffer_id

class packet:
    """Class to manipulate packet

    @author ykk
    @date June 2011
    """
    def __init__(self, dpkt=None):
        """Initialize
        """
        ##Reference to packet
        self.dpkt = dpkt
    
    def nw_rewrite(self, rewrite_src, addr):
        """Add rewrite for IP address

        @param rewrite_src boolean for indicated rewrite src or dst
        @param addr address to rewrite to
        @return success or not
        """
        if (self.dpkt != None):
            pktact.nw_rewrite(rewrite_src, addr)
            return True
        return False

    def dl_rewrite(self, rewrite_src, addr):
        """Add rewrite for Ethernet address

        @param rewrite_src boolean for indicated rewrite src or dst
        @param addr address to rewrite to
        @return success or not
        """
        if (self.dpkt != None):
            pktact.dl_rewrite(rewrite_src, addr)
            return True

        return False
            
class flow_entry(actions, packet):
    """Class to provide some pre-formed flow entry

    @author ykk
    @date Feb 2011
    """
    NONE = 0
    DROP = 0
    GET = 1
    FLOOD = 2
    def __init__(self, action=NONE, pkt=None):
        """Initialize

        @param action NONE (default), DROP, GET, FLOOD
        @param packet dpkt parsed packet
        """
        actions.__init__(self)
        packet.__init__(self, pkt)
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

    def add_nw_rewrite(self, rewrite_src, addr):
        """Add rewrite for IP address (and rewrite packet if available)

        @param rewrite_src boolean for indicated rewrite src or dst
        @param addr address to rewrite to
        """
        actions.add_nw_rewrite(self, rewrite_src, addr)
        packet.nw_rewrite(self, rewrite_src, addr)

    def add_dl_rewrite(self, rewrite_src, addr):
        """Add rewrite for Ethernet address (and rewrite packet if available)

        @param rewrite_src boolean for indicated rewrite src or dst
        @param addr address to rewrite to
        """
        actions.add_dl_rewrite(self, rewrite_src, addr)
        packet.dl_rewrite(self, rewrite_src, addr)

    def set_in_port(self, in_port):
        """Set in_port in match

        @param in_port value of in_port
        """
        self.match.wildcards = self.match.wildcards & ~pyof.OFPFW_IN_PORT
        self.match.in_port = in_port

    def set_dl_src(self, src_mac):
        """Set source mac address in match

        @param src_mac value of Ethernet address
        """
        self.match.wildcards = self.match.wildcards & ~pyof.OFPFW_DL_SRC
        self.match.dl_src = src_mac

    def set_dl_dst(self, dst_mac):
        """Set destination mac address in match
        
        @param dst_mac value of Ethernet address
        """
        self.match.wildcards = self.match.wildcards & ~pyof.OFPFW_DL_DST
        self.match.dl_dst = dst_mac

    def set_nw_src(self, src_ip):
        """Set source IP in match

        @param src_ip value of IP address
        """
        self.match.wildcards = self.match.wildcards & ~pyof.OFPFW_NW_SRC_ALL
        self.match.nw_src = src_ip

    def set_nw_dst(self, dst_ip):
        """Set destination IP in match
        
        @param dst_ip value of IP address
        """
        self.match.wildcards = self.match.wildcards & ~pyof.OFPFW_NW_DST_ALL
        self.match.nw_dst = dst_ip

    def set_tp_src(self, tp_src):
        """Set source IP in match
        
        @param tp_src source transport port
        """
        self.match.wildcards = self.match.wildcards & ~pyof.OFPFW_TP_SRC
        self.match.tp_src = tp_src

    def set_tp_dst(self, tp_dst):
        """Set destination IP in match
        
        @param tp_dst destination transport port
        """
        self.match.wildcards = self.match.wildcards & ~pyof.OFPFW_TP_DST
        self.match.tp_dst = tp_dst

    def reverse(self, in_port):
        """Compute the reverse flow

        Heavily wildcarded except for addresses and ports
        
        @param in_port in port of the reverse flow
        @return reverse flow
        """
        fe = flow_entry()

        fe.match.wildcards = pyof.OFPFW_ALL - pyof.OFPFW_IN_PORT - \
            pyof.OFPFW_DL_SRC - pyof.OFPFW_DL_DST
        fe.match.in_port = in_port
        fe.match.dl_src = self.match.dl_dst
        fe.match.dl_dst = self.match.dl_src       

        if (self.match.dl_type == dpkt.ethernet.ETH_TYPE_IP):
            fe.match.wildcards = fe.match.wildcards - pyof.OFPFW_DL_TYPE - \
                pyof.OFPFW_NW_SRC_ALL - pyof.OFPFW_NW_DST_ALL
            fe.match.dl_type = self.match.dl_type
            fe.match.nw_src = self.match.nw_dst
            fe.match.nw_dst = self.match.nw_src
            
        if (self.match.nw_proto == dpkt.ip.IP_PROTO_TCP or 
            self.match.nw_proto == dpkt.ip.IP_PROTO_UDP):
            fe.match.wildcards = fe.match.wildcards - pyof.OFPFW_NW_PROTO -\
                pyof.OFPFW_TP_SRC - pyof.OFPFW_TP_DST
            fe.match.nw_proto = self.match.nw_proto
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

    def _set_flow_mod_flag(self, mask, set_flag):
        """Set flow mod flag
        
        @param mask to use for flag
        @param set_flag set flag to true or false
        """
        if (set_flag):
            self.flags = self.flags | mask
        else:           
            self.flags = self.flags & (~mask)

    def set_flow_removed_flag(self, send_flow_removed=True):
        """Set flow removed flags
        
        @param send_flow_removed set or not
        """
        self._set_flow_mod_flag(pyof.OFPFF_SEND_FLOW_REM, send_flow_removed)

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

    def install(self, conn, sock, command=pyof.OFPFC_MODIFY):
        """Install flow
        
        @param conn OpenFlow connections
        @param sock reference socket
        @param command command for flow mod
        """
        self.install_flow(conn.db[sock], command=pyof.OFPFC_MODIFY)

    def install_flow(self, conn, command):
        """Install flow
        
        @param conn OpenFlow connection
        @param command command for flow mod
        """
        conn.send(self.get_flow_mod(command).pack())
        if ((self.buffer_id != UNBUFFERED_ID) and (self.dpkt != None)):
            conn.send(self.get_packet_out().pack()+self.dpkt.pack())

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

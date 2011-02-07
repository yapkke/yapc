##OpenFlow specific library
#
# Generate OpenFlow information
#
# @author ykk
# @date Feb 2011
#
import dpkt
import struct
import socket
import yapc.pyopenflow as pyof
import yapc.output as output

##Next transaction id to use
last_xid = 0

##VLAN Tag parsing
VLAN_PRIORITY_MASK = 0xe000
VLAN_PRIORITY_SHIFT = 13
VLAN_ID_MASK = 0x0fff

def get_xid():
    """Retrieve XID to use
    """
    global last_xid
    last_xid += 1
    return last_xid

def get_ofp_match(in_port, packet):
    """Generate ofp_match from raw packet

    Note that OpenFlow uses outermost Ethertype, while dokt provides
    the innermost one.  And VLAN tag parsing is manually done.

    @param in_port input port of packet
    @param packet raw packet
    @return (ofp match, dpkt's packet)
    """
    ofm = pyof.ofp_match()
    pkt = dpkt.ethernet.Ethernet(packet)
    
    #In Port
    ofm.in_port = in_port

    #Get Ethernet
    ofm.dl_src = byte_str2array(pkt.src)
    ofm.dl_dst = byte_str2array(pkt.dst)
    ofm.dl_type = struct.unpack('>H',packet[12:14])[0]

    #802.1Q VLAN
    if (ofm.dl_type == dpkt.ethernet.ETH_TYPE_8021Q):
        ofm.dl_vlan = pkt.tag & VLAN_ID_MASK
        ofm.dl_vlan_pcp = (pkt.tag & VLAN_PRIORITY_MASK) >> VLAN_PRIORITY_SHIFT

    #Get IP if any
    if (isinstance(pkt.data, dpkt.ip.IP)):
        __get_ip_ofp_match(ofm, pkt.data)
    elif (isinstance(pkt.data, dpkt.arp.ARP)):
        __get_arp_ofp_match(ofm, pkt.data)

    return (ofm, pkt)

def __get_arp_ofp_match(ofm, arppkt):
    """Get ofp_match for ARP

    @param ofm ofp_match to populate
    @param arppkt dpkt's ARP packet
    @return ofp match
    """
    #Get ARP
    ofm.nw_src = struct.unpack("!L",arppkt.spa)[0]
    ofm.nw_dst = struct.unpack("!L",arppkt.tpa)[0]   
    ofm.nw_proto = arppkt.op

    return ofm


def __get_ip_ofp_match(ofm, ippkt):
    """Get ofp_match for IP

    @param ofm ofp_match to populate
    @param ippkt dpkt's IP packet
    @return ofp match
    """
    #Get IP
    ofm.nw_src = struct.unpack("!L",ippkt.src)[0]
    ofm.nw_dst = struct.unpack("!L",ippkt.dst)[0]
    ofm.nw_tos = ippkt.tos
    ofm.nw_proto = ippkt.p

    #Get TCP if any
    if (isinstance(ippkt.data, dpkt.tcp.TCP)):
        __get_tcp_ofp_match(ofm, ippkt.data)
    elif (isinstance(ippkt.data, dpkt.udp.UDP)):
        __get_udp_ofp_match(ofm, ippkt.data)
    elif (isinstance(ippkt.data, dpkt.icmp.ICMP)):
        __get_icmp_ofp_match(ofm, ippkt.data)

    return ofm
    
def __get_icmp_ofp_match(ofm, icmppkt):
    """Get ofp_match for ICMP

    @param ofm ofp_match to populate
    @param icmppkt dpkt's ICMP packet
    @return ofp match
    """
    #Get ICMP
    ofm.tp_src = icmppkt.type
    ofm.tp_dst = icmppkt.code
    return ofm

def __get_tcp_ofp_match(ofm, tcppkt):
    """Get ofp_match for TCP

    @param ofm ofp_match to populate
    @param tcppkt dpkt's TCP packet
    @return ofp match
    """
    #Get TCP
    ofm.tp_src = tcppkt.sport
    ofm.tp_dst = tcppkt.dport
    return ofm

def __get_udp_ofp_match(ofm, udppkt):
    """Get ofp_match for UDP

    @param ofm ofp_match to populate
    @param udppkt dpkt's UDP packet
    @return ofp match
    """
    #Get TCP
    ofm.tp_src = udppkt.sport
    ofm.tp_dst = udppkt.dport
    return ofm


def byte_str2array(str):
    """Convert binary str to array

    @param str binary string
    @return array of values
    """
    r = []
    for i in range(0, len(str)):
        r.append(struct.unpack("B", str[i])[0])
    return r

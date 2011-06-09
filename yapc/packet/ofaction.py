##Module to implement OpenFlow actions on a packet (dpkt)
#
# Expects dpkt.ethernet.Ethernet packet ('cos OpenFlow fights Ethernet packets)
#
# @author ykk
# @date Jun 2011
#
import dpkt
import yapc.util.parse as pu

def nw_rewrite(pkt, rewrite_src, addr):
    """Rewrite network address

    Handles ARP packets (spa and tpa address)

    @param pkt dpkt.ethernet.Ethernet packet
    @param rewrite_src boolean for indicated rewrite src or dst
    @param addr address to rewrite to (ip in absolute value)
    @return True is rewritten
    """
    address = pu.ip_val2binary(addr)

    if (pkt["type"] == dpkt.ethernet.ETH_TYPE_IP):
        #Set sum to 0 else pack will produce the wrong checksum
        setattr(pkt["data"], "sum", 0)
        #Set UDP checksum
        if (pkt["data"].p == 6 or pkt["data"].p == 17): ##TCP or UDP
            setattr(pkt["data"]["data"], "sum", 0)

        if (rewrite_src):
            setattr(pkt["data"], "src", address)
        else:
            setattr(pkt["data"], "dst", address)
        return True

    if (pkt["type"] == dpkt.ethernet.ETH_TYPE_ARP):
        if (rewrite_src):
            setattr(pkt["data"], "spa", address)
        else:
            setattr(pkt["data"], "tpa", address)
        return True

    return False

def dl_rewrite(pkt, rewrite_src, addr):
    """Rewrite network address

    Handles ARP packets (exact sha and tha fields)

    @param pkt dpkt.ethernet.Ethernet packet
    @param rewrite_src boolean for indicated rewrite src or dst
    @param addr address to rewrite to (array of byte)
    @return True
    """
    address = pu.array2byte_str(addr)

    if (rewrite_src):
        setattr(pkt, "src", address)
    else:
        setattr(pkt, "dst", address)

    if (pkt["type"] == dpkt.ethernet.ETH_TYPE_ARP):
        if (rewrite_src):
            setattr(pkt["data"], "sha", address)
        else:
            setattr(pkt["data"], "tha", address)

    return True

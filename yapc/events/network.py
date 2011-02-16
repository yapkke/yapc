##Network events
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.output as output

class link_event(yapc.event):
    """Event to indicate link up

    @author ykk
    @date Feb 2011
    """
    name = "Network Link Event"
    def __init__(self, src_dpid, src_port,
                 dst_dpid, dst_port):
        """Initialize

        @param src_dpid DPID of source
        @param src_port port number of source
        @param dst_dpid DPID of destination
        @param dst_port port number of destination
        """
        self.src_dpid = src_dpid
        self.src_port = src_port
        self.dst_dpid = dst_dpid
        self.dst_port = dst_port
        output.dbg("Link event of %x" % src_dpid +\
                   ":"+str(src_port)+\
                   " to %x" % dst_dpid +\
                   ":"+str(dst_port),
                   self.__class__.__name__)
    
class link_down(link_event):
    """Event to indicate link down

    @author ykk
    @date Feb 2011
    """
    name = "Network Link Down"

class link_up(link_event):
    """Event to indicate link down

    @author ykk
    @date Feb 2011
    """
    name = "Network Link Up"

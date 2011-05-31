##Network protocol
#
# Implement network protocols at the local host
#
# @author ykk
# @date May 2011
#
import yapc.interface as yapc
import yapc.log.output as output
import yapc.events.openflow as ofevents
import yapc.util.memcacheutil as mcutil
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
        mc.get_client()
        ##OpenFlow connections
        self.ofconnections = ofconn
        
        server.register_event_handler(ofevents.pktin.name,
                                      self)

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
        
        
        return True


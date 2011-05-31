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
import dpkt

class dhcp(yapc.component):
    """Component that sends and interprets DHCP packets from interfaces on switch

    Record of IP address and gateway saved in memcache
    
    @author ykk
    @date May 2011
    """
    def __init__(self, server, ofconn):
        """Initialize

        @param server yapc core server/scheduler
        @param ofconn OpenFlow connections
        """
        ##OpenFlow connections
        self.ofconnections = ofconn
        
        server.register_event_handler(ofevents.pktin.name,
                                      self)

    def processevent(self, event):
        """Process OpenFlow messages

        @param event event to handle
        @return True for everything other than DHCP reply
        """
        
        
        return True


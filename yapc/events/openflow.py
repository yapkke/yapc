##Generic OpenFlow events
#
# 
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.output as output
import yapc.ofcomm as ofcomm
import yapc.pyopenflow as pyof
import yapc.openflowutil as ofutil

class parser(yapc.component):
    """OpenFlow parser that generates OpenFlow events
    
    @author ykk
    @date Feb 2011
    """
    def __init__(self, server):
        """Initialize
        
        @param server yapc core
        """
        ##Reference to scheduler
        self.scheduler = server

        server.register_event_handler(ofcomm.message.name, self)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        """
        if (isinstance(event, ofcomm.message)):
            if (event.header.type == pyof.OFPT_PACKET_IN):
                self.scheduler.post_event(pktin(event.sock,
                                                event.message))

        return True


class pktin(ofcomm.message):
    """Packet in event in OpenFlow

    @author ykk
    @date Feb 2011
    """
    name = "OpenFlow Packet In"
    def __init__(self, sock, msg):
        """Initialize

        @param sock reference to socket
        @param msg message
        """
        ofcomm.message.__init__(self, sock, msg)

        ##Packet in header
        self.pktin = None
        ##Packet included parsed by dpkt
        self.dpkt = None
        ##Binary packet
        self.pkt = None
        ##Exact match for match
        self.match = None

        if (self.header.type == pyof.OFPT_PACKET_IN):
            self.pktin = pyof.ofp_packet_in()
            self.pkt = self.pktin.unpack(msg)
            output.vdbg("Packet in\n"+self.pktin.show("\t"),
                        self.__class__.__name__)
            (self.match, self.dpkt) = ofutil.get_ofp_match(self.pktin.in_port, 
                                                           self.pkt)
            output.vdbg("Packet has match\n"+self.match.show("\t"),
                        self.__class__.__name__)
            output.vdbg(str(`self.dpkt`),
                        self.__class__.__name__)
    
        

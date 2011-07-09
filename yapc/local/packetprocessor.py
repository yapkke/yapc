##Base for local packet processing
#
# Get packets and manipulate them
#
# @author ykk
# @date July 2011
#
import yapc.interface as yapc
import yapc.comm.raw as rawcomm
import yapc.log.output as output

class base(yapc.component):
    """Base class for packet processor
    
    Get message from raw socket for per packet processing

    @author ykk
    @date July 2011
    """
    def __init__(self, server, rawsock=None):
        """Initialize
        
        If rawsock is None, the component will grab all 
        yapc.comm.raw.message.  Else, it would make the
        yapc.comm.raw.rawsocket exclusive to this handler.

        @param server reference to yapc core
        @param rawsock rawsocket to handle
        """
        if (rawsock == None):
            server.register_event_handler(rawcomm.message.name, self)
        else:
            rawsock.mgr.make_priv(self)

    def add_sock(self, rawsock):
        """Add socket for private/exclusive handling

        @param rawsock rawsocket to handle
        """
        rawsock.mgr.make_priv(self)

    def processevent(self, event):
        """Process event

        @param event event to process
        """
        if isinstance(event, rawcomm.message):
            return self.processpacket(event)
        elif (isinstance(event, yapc.priv_callback) and 
              isinstance(event.magic, rawcomm.message)):
            return self.processpacket(event.magic)
 
    def processpacket(self, rawmsg):
        """Main function of the packet processor

        To be overriden
        """
        return True

class bitw(base):
    """A base class for Bump-in-the-wire
    
    @author ykk
    @date July 2011
    """
    def __init__(self, server, intf1, intf2):
        """Initialize

        @param server reference to yapc core
        @param intf1 name of interface 1 to attach bump in the wire
        @param intf2 name of interface 2 to attach bump in the wire
        """
        ##Reference to first interface
        self.intf1 = rawcomm.rawsocket(server, intf1)
        ##Reference to second interface
        self.intf2 = rawcomm.rawsocket(server, intf2, rawmgr=self.intf1.mgr)
        ##Constructor
        base.__init__(self, server, self.intf1)

    def processpacket(self, rawmsg):
        """Process packet

        Simply send on the other side
        """
        pkt = process(rawmsg.message)
        if (rawmsg.sock == self.intf1.sock):
            self.intf2.sock.send(pkt)
        if (rawmsg.sock == self.intf2.sock):
            self.intf1.sock.send(pkt)
        
        return True

    def process(self, packet):
        """Process packet

        Does nothing (to be overridden)

        @param packet packet received
        @return packet to send
        """
        return packet
        

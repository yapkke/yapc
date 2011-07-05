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
    
    Get message from 

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

    def processevent(self, event):
        """Process event

        @param event event to process
        """
        if isinstance(event, rawcomm.message):
            self.processpacket(event)
        elif (isinstance(event, yapc.priv_event) and 
              isinstance(event.magic, rawcomm.message)):
            self.processpacket(event.magic)
            
    def processpacket(self, rawmsg):
        """Main function of the packet processor

        To be overriden
        """
        pass

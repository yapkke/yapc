##Components for debugging OpenFlow
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.comm.openflow as ofcomm
import yapc.output as output

class of_msg_count(yapc.component):
    """Component to count number of OpenFlow messages in a second
    
    @author ykk
    @date Feb 2011
    """
    def __init__(self, server, period=5):
        """Initialize

        @param server yapc core
        @param period period before each printout
        """
        ##Reference to scheduler for timed events
        self.server = server
        server.register_event_handler(ofcomm.message.name,
                                      self)
        ##Count for number of messages
        self.count = 0
        ##How often to count
        self.period = period
        self.server.post_event(yapc.priv_callback(self, None),
                               self.period)
    
    def processevent(self, event):
        """Handle event
        """
        if (isinstance(event, yapc.priv_callback)):
            #Timer up
            self.server.post_event(yapc.priv_callback(self, None),
                                   self.period)

            output.info("yapc sees "+str(self.count)+" OpenFlow messages in the last "+\
                        str(self.period)+" seconds",
                       self.__class__.__name__)
            self.count = 0
        elif (isinstance(event, ofcomm.message)):
            self.count += 1
            
        return True

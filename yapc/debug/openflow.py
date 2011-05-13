##Components for debugging OpenFlow
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.comm.openflow as ofcomm
import yapc.output as output
import yapc.events.openflow as ofevents

class show_flow_removed(yapc.component):
    """Component to print flow removed

    @author ykk
    @date May 2011
    """
    def __init__(self, server):
        """Initialize

        @param server yapc core
        """
        server.register_event_handler(ofevents.flow_removed.name, self)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        @return false if flow can be installed, else true
        """
        if (isinstance(event, ofevents.flow_removed)):
            output.info("Received flow removed:\n"+event.flowrm.show("\t"),
                        self.__class__.__name__);
        
        return True

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

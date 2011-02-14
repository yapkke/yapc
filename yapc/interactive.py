##Interactive components
#
# @author ykk
# @date Feb 2011
#

import yapc.interface as yapc

class event_queue(yapc.component):
    """Class to queue OpenFlow

    @author ykk
    @date Feb 2011
    """
    def __init__(self, server, eventname):
        """Initialize

        @param server yapc core
        @param eventname name of event to queue
        """
        ##Event queue
        self.queue = []
        
        server.register_event_handler(eventname, self)

    def processevent(self, event):
        """Process event

        @param event to process
        """
        self.queue.append(event)
        
        return True

    def __len__(self):
        """Length of event queue

        @return length of current queue
        """
        return len(self.queue)


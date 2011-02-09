## YAPC core
#
# Yet Another Python Controller's core
#
# @author ykk
# @date Oct 2010
#
import time
import os
import sys
import signal
import yapc.comm as comm
import yapc.ofcomm as ofcomm
import yapc.output as output

class eventdispatcher:
    """Core event dispatcher for YAPC
    
    @author ykk
    @date Oct 2010
    """
    def __init__(self):
        """Initialize
        """
        ##Event queue
        self.__events = []
        ##Event processing registration
        self.__processors = {}
        ##List of shutdown components
        self.cleanups = []

    def len(self):
        """Return length of current event queue
        """
        return len(self.__events)

    def cleanup(self):
        """Clean up run
        """
        for shutdown in self.cleanups:
            shutdown.cleanup()

    def registercleanup(self, shutdown):
        """Register shutdown
        
        @param shutdown cleanup function to register
        """
        self.cleanups.insert(0,shutdown)

    def registereventhandler(self, eventname, handler):
        """Register handler for event
        
        Event should be registered in order of calling
        @param eventname name of event
        @param handler handler function
        """
        if (not isinstance(eventname, str)):
            output.warn("Event name "+str(eventname)+" is not  a string",
                        self.__class__.__name__)
            return
        #Register handler
        if (eventname not in self.__processors):
            self.__processors[eventname] = []
        self.__processors[eventname].append(handler)

    def print_event_and_handler(self):
        """Print event and handlers as debug messages
        """
        for event,handlers in self.__processors.items():
            pout = "Event "+event+" is handled in order by \n"
            for h in handlers:
                pout += "\t"+h.__class__.__name__+"\n"
            output.dbg(pout, self.__class__.__name__)

    def postevent(self, event):
        """Post event

        @param event event to post
        """
        self.__events.append(event)
        output.vdbg("Post "+str(event),
                   self.__class__.__name__)
        
    def dispatchnextevent(self):
        """Dispatch next event
        """
        if (len(self.__events) != 0):
            event = self.__events.pop(0)
            try:
                for handler in self.__processors[event.name]:
                    output.vdbg("Dispatch "+event.name+\
                                    " to "+handler.__class__.__name__,
                                self.__class__.__name__)
                    try:
                        r = handler.processevent(event)
                        if (r == None):
                            output.warn(handler.__class__.__name__+"'s "+\
                                            "processevent method should return"+\
                                            " True/False (using True by default)",
                                        self.__class__.__name__)
                            r = True
                        if (not r):
                            break;
                    except:
                        output.output("CRITICAL",
                                      "Error occurs here... going to clean up",
                                      self.__class__.__name__)
                        self.cleanup()
                        raise
            except KeyError:
                #No handler, so pass
                output.warn("Event "+str(event.name)+" does not have handler",
                            self.__class__.__name__)

class server:
    """Daemon for yapc core

    @author ykk
    @date Oct 2010
    """
    def __init__(self):
        """Initialize
        """
        #Amount to sleep
        self.sleep = 0.1
        #Last start time
        self.__starttime = time.clock()
        ##Indicate if running
        self.running = True
        ##Event scheduler
        self.scheduler = eventdispatcher()
        ##Receive thread
        self.recv = comm.receivethread()
        self.recv.start()
        ##Register for signal
        signal.signal(signal.SIGINT, self.signalhandler)
        signal.signal(signal.SIGTERM, self.signalhandler)
       
    def run(self):
        """Main loop to run
        """
        #Output events and handlers
        self.scheduler.print_event_and_handler()
        #Run
        while self.running:
            self.__starttime = time.clock()
            self.scheduler.dispatchnextevent()

            #Sleep if looping too fast
            sleeptime = self.sleep-(time.clock()-self.__starttime)
            if (sleeptime > 0):
                time.sleep(sleeptime)

    def signalhandler(self, signal, frame):
        """Handle signal
        """
        self.scheduler.cleanup()
        output.info("Exiting yapc...", self.__class__.__name__)
        sys.exit(0)

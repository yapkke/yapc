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
import bisect
import yapc.comm as comm
import yapc.ofcomm as ofcomm
import yapc.output as output
import yapc.interface as yapc

class eventqueue:
    """Queue to hold timed event

    @author ykk
    @date Feb 2011
    """
    def __init__(self):
        """Initialize
        """
        ##Internal queue for events
        self.__events = []
        ##Internal queue for time
        self.__time = []

    def __len__(self):
        """Length of queue
        """
        return len(self.__events)

    def add(self, event, clock):
        """Add event
        
        @param event event to add
        @param clock time to dispatch (based on time.time())
        """
        p = bisect.bisect(self.__time, clock)
        bisect.insort(self.__time, clock)
        self.__events.insert(p, event)
        output.vvdbg(str(event)+" inserted for dispatch at time "+str(clock),
                     self.__class__.__name__)

    def get_events(self):
        """Retrieve clone of event queue
        """
        r = self.__events[:]
        return r

    def get_time(self):
        """Retrieve clone of event time
        """
        r = self.__time[:]
        return r

    def get_next_time(self):
        """Retrieve time of next event
        """
        if (len(self.__time) == 0):
            return None

        return self.__time[0]

    def has_event_ready(self):
        """Indicate if there is any event ready to run
        """
        t = self.get_next_time()
        if (t == None):
            return False
        else:
            return (t <= time.time())

    def get_next(self):
        """Get next time and event
        
        @return tuple of time and event
        """
        t = self.__time.pop(0)
        e = self.__events.pop(0)
        return (t,e)

class eventdispatcher:
    """Core event dispatcher for YAPC
    
    @author ykk
    @date Oct 2010
    """
    def __init__(self, tolerance=0.01):
        """Initialize

        @param tolerance time tolerance before printing warnings (default=10 ms)
        """
        ##Event queue
        self.__events = []
        ##Timed event queue
        self.__timedevents = eventqueue()
        ##Event processing registration
        self.__processors = {}
        ##List of shutdown components
        self.cleanups = []
        ##Tolerance for timing
        self.tolerance = tolerance

    def __len__(self):
        """Return length of current non-timed event queue
        """
        return len(self.__timedevents)

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

    def postevent(self, event, timedelta=0):
        """Post event

        @param event event to post
        @param timedelta to wait before posting event
        """
        #Check event is an event
        if (not isinstance(event, yapc.event)):
            output.warn(str(event)+"is not an event",
                        self.__class__.__name__)
            return

        if (timedelta == 0):
            self.__events.append(event)
            output.vvdbg("Post "+str(event),
                         self.__class__.__name__)
        elif (timedelta > 0):
            clock = time.time() + timedelta
            self.__timedevents.add(event, clock)
        else:
            output.warn("Cannot schedule event "+str(event)+" to the past")

    def has_event_ready(self):
        """Indicate if there is any event ready to run
        """
        return (len(self.__events) > 0 or
                self.__timedevents.has_event_ready())
        
    def get_next_time(self):
        """Get next time in timed event queue
        """
        return self.__timedevents.get_next_time()

    def __handle_event(self, handler, event):
        """Handle event
        
        @param handler handler for event
        @param event event
        """
        try:
            r = handler.processevent(event)
            if (r == None):
                output.warn(handler.__class__.__name__+"'s "+\
                                "processevent method should return"+\
                                " True/False (using True by default)",
                            self.__class__.__name__)
                r = True
        except:
            output.output("CRITICAL",
                          "Error occurs here... going to clean up",
                          self.__class__.__name__)
            self.cleanup()
            raise
        return r

    def dispatchnextevent(self):
        """Dispatch next event
        """
        #Get timed event if valid
        event = None
        t = self.__timedevents.get_next_time()
        c = time.time()
        if (t != None and t <= c):
            (tim, event) = self.__timedevents.get_next()
            if ((c-tim) > self.tolerance):
                output.warn("Event "+event.name+" scheduled for time "+\
                                str(tim)+" is running at time "+str(c),
                            self.__class__.__name__)
            else:
                output.vvdbg("Event "+event.name+" scheduled for time "+\
                                 str(tim)+" is running at time "+str(c),
                             self.__class__.__name__)

        #If no timed event, get non-timed event
        if (event == None and len(self.__events) != 0):
            event = self.__events.pop(0)

        if (event == None):
            return

        #Dispatch event
        if (isinstance(event, yapc.priv_event)):
            self.__handle_event(event.handler, event.event)
        else:
            try:
                for handler in self.__processors[event.name]:
                    output.vvdbg("Dispatch "+event.name+\
                                     " to "+handler.__class__.__name__,
                                 self.__class__.__name__)
                    if (not self.__handle_event(handler, event)):
                        break
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
        self.__starttime = time.time()
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
            self.__starttime = time.time()
            
            while (self.scheduler.has_event_ready()):
                self.scheduler.dispatchnextevent()

            #Sleep if looping too fast
            nexttimedevent = self.scheduler.get_next_time()
            maxsleeptime = self.sleep
            if (nexttimedevent != None):
                maxsleeptime = nexttimedevent-time.time()
            sleeptime = min(maxsleeptime, 
                            self.sleep-(time.time()-self.__starttime))
            if (sleeptime > 0):
                output.vvdbg("Sleeping for "+str(sleeptime)+" seconds"+\
                                 " with "+str(len(self.scheduler))+" timed events"+\
                                 " for running at "+str(self.scheduler.get_next_time())+\
                                 " "+str(time.time()),
                             self.__class__.__name__)
                time.sleep(sleeptime)

    def signalhandler(self, signal, frame):
        """Handle signal
        """
        self.scheduler.cleanup()
        output.info("Exiting yapc...", self.__class__.__name__)
        sys.exit(0)

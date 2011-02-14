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
import threading
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

        @return list of events
        """
        r = self.__events[:]
        return r

    def get_time(self):
        """Retrieve clone of event time

        @return list of time
        """
        r = self.__time[:]
        return r

    def get_next_time(self):
        """Retrieve time of next event

        @return next event's time
        """
        if (len(self.__time) == 0):
            return None

        return self.__time[0]

    def has_event_ready(self):
        """Indicate if there is any event ready to run

        @return if there is event to run
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

class dispatcher(threading.Thread):
    """Dispatcher class to dispacth events

    @author ykk
    @date Feb 2011
    """
    def __init__(self, cleanup,
                 processors=None, event_queue=None):
        """Initialize

        @param cleanup reference to master cleanup
        @param processors reference to processors if any
        @param event_queue reference to event queue if any
        """
        threading.Thread.__init__(self)
        ##Reference to cleanup component
        self.cleanup = cleanup
        ##Event queue
        if (event_queue == None):
            self._events = []
        else:
            self._events = event_queue
        ##Event processing registration
        if (processors == None):
            self._processors = {}
        else:
            self._processors = processors
        ##Max amount of time to sleep
        self.sleep = 0.1
        ##Indicate if runing
        self.running = True

    def __len__(self):
        """Return length of current event queue

        @return length of event queue
        """
        return len(self._events)

    def print_event_handlers(self):
        """Output event and handlers for it
        """
        for e,handles in self._processors.items():
            output.dbg("Event "+e+" in order handled by:",
                       self.__class__.__name__)
            for h in handles:
                output.dbg("\t"+h.__class__.__name__,
                           self.__class__.__name__)
                
    def order_handler(self, eventname, 
                      earlier_handler, later_handler):
        """Order handler for given event

        Do so by moving earlier handler to be just before the later handler

        @param eventname name of event
        @param earlier_handler handler that should process event earlier
        @param later_handler handler that should process event later
        """
        #Get event handlers
        if (eventname not in self._processors):
            output.warn("Shuffle handlers of unknown event "+eventname,
                        self.__class__.__name__)
        h = self._processors[eventname]

        eindex = -1
        if (earlier_handler in h):
            eindex = h.index(earlier_handler)
        else:
            output.warn(earlier_handler.__class__.__name__+\
                        "is not a handler of event "+eventname,
                        self.__class__.__name__)
            return

        lindex = -1
        if (later_handler in h):
            lindex = h.index(later_handler)
        else:
            output.warn(later_handler.__class__.__name__+\
                        "is not a handler of event "+eventname,
                        self.__class__.__name__)
            return

        #Reorder
        if (lindex < eindex):
            h.insert(lindex, h.pop(eindex))

    def _dispatch_event(self, event):
        """Dispatch next event

        @param event event to dispatch
        """
        #Dispatch event
        if (isinstance(event, yapc.priv_callback)):
            self.__handle_event(event.handler, event)
            output.vvdbg("Event "+event.name+" dispatched to "+
                         event.handler.__class__.__name__,
                         self.__class__.__name__)
        else:
            try:
                for handler in self._processors[event.name]:
                    output.vvdbg("Dispatch "+event.name+\
                                     " to "+handler.__class__.__name__,
                                 self.__class__.__name__)
                    if (not self.__handle_event(handler, event)):
                        break
            except KeyError:
                #No handler, so pass
                output.warn("Event "+str(event.name)+" does not have handler",
                            self.__class__.__name__)

    def __handle_event(self, handler, event):
        """Handle event
        
        @param handler handler for event
        @param event event
        @return if to pass on to next handler
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
            self.cleanup.cleanup()
            raise
        return r

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
        if (eventname not in self._processors):
            self._processors[eventname] = []
        self._processors[eventname].append(handler)

class event_dispatcher(dispatcher):
    """Class to dispatch non-timed event

    @author ykk
    @date Feb 2011
    """
    def __init__(self, cleanup, processors=None):
        """Initialize

        @param cleanup master cleanup component
        @param processors reference to processors/handlers if any
        """
        dispatcher.__init__(self, cleanup, processors)
        ##Just a record of starting time of each loop
        self.__starttime = time.time()

    def post_event(self, event):
        """Post event

        @param event event to post
        @return success status (always True)
        """
        self._events.append(event)
        return True

    def run(self):
        """Main loop
        """
        while self.running:
            self.__starttime = time.time()

            while (len(self) > 0):
                self._dispatch_event(self._events.pop(0))

            sleeptime = self.sleep-(time.time()-self.__starttime)
            if (sleeptime > 0):
                time.sleep(sleeptime)

class timed_event_dispatcher(dispatcher):
    """Class to dispatch timed event

    @author ykk
    @date Feb 2011
    """
    def __init__(self, cleanup, processors=None, tolerance=0.1):
        """Initalize

        @param cleanup master cleanup component
        @param processors reference to processors/handlers if any
        @param tolerance tolerance to timing
        """
        dispatcher.__init__(self, cleanup, processors,
                            eventqueue())
        ##Reference to tolerance
        self.tolerance = tolerance

    def post_event(self, event, clock):
        """Post event

        @param event event to post
        @param clock time to post event
        @return success status
        """
        if (clock > (time.time()+self.sleep)):
            self._events.add(event, clock)
            output.vvdbg("Added event "+event.name+" for time "+str(clock),
                         self.__class__.__name__)
            return True
        else:
            output.warn("Cannot add event "+event.name+\
                        " shorter than "+str(self.sleep)+\
                        " before execution time",
                        self.__class__.__name__)
            return False

    def run(self):
        """Main loop
        """
        while self.running:
            if (len(self._events) == 0):
                #Sleep for some time if nothing to do
                time.sleep(self.sleep)
                continue
            else:
                while (self._events.has_event_ready()):
                    (t, event) = self._events.get_next()
                    if ((t-time.time()) > self.tolerance):
                        output.warn("Event "+event.name+" scheduled for "+str(t)+\
                                    " is being run at time "+str(time.time()),
                                    self.__class__.__name__)
                    else:
                        output.vvdbg("Event "+event.name+" scheduled for "+str(t)+\
                                     " is being run at time "+str(time.time()),
                                     self.__class__.__name__)
                    self._dispatch_event(event)

            ntime = self.sleep
            if (len(self._events) > 0):
                ntime = self._events.get_next_time() - time.time()
            time.sleep(min(ntime, self.sleep))

class core:
    """yapc core

    @author ykk
    @date Oct 2010
    """
    def __init__(self):
        """Initialize
        """
        ##Event scheduler
        self.__scheduler = event_dispatcher(self,)
        ##Timed Event scheduler
        self.__timedscheduler = timed_event_dispatcher(self,
                                                       self.__scheduler._processors)
        ##Receive thread
        self.recv = comm.receivethread()
        ##List of shutdown components
        self.cleanups = []
        ##Register for signal
        signal.signal(signal.SIGINT, self.signalhandler)
        signal.signal(signal.SIGTERM, self.signalhandler)

    def register_event_handler(self, eventname, handler):
        """Register handler for event
        
        Event should be registered in order of calling
        @param eventname name of event
        @param handler handler function
        """
        self.__scheduler.registereventhandler(eventname,
                                              handler)

    def post_event(self, event, timedelta = 0):
        """Post event

        @param event event to post
        @param timedelta to wait before posting event
        @return if successful
        """
        #Check event is an event
        if (not isinstance(event, yapc.event)):
            output.warn(str(event)+"is not an event",
                        self.__class__.__name__)

        if (timedelta == 0):
            return self.__scheduler.post_event(event)
        else:
            return self.__timedscheduler.post_event(event,
                                                    timedelta+time.time())

    def register_cleanup(self, shutdown):
        """Register shutdown
        
        @param shutdown cleanup function to register
        """
        self.cleanups.insert(0,shutdown)

    def print_event_handlers(self):
        """Print the current event and handlers
        """
        self.__scheduler.print_event_handlers()

    def run(self, runbg=False):
        """Run core

        @param runbg runs everything as thread in background
        """
        self.__scheduler.print_event_handlers()

        self.recv.start()
        self.__timedscheduler.start()
        if (runbg):
            self.__scheduler.start()
        else:
            self.__scheduler.run()

    def order_handler(self, eventname, 
                      earlier_handler, later_handler):
        """Order handler for given event

        Do so by moving earlier handler to be just before the later handler

        @param eventname name of event
        @param earlier_handler handler that should process event earlier
        @param later_handler handler that should process event later
        """
        self.__scheduler.order_handler(eventname, 
                                       earlier_handler, later_handler)
        
    def cleanup(self):
        """Clean up
        """
        output.dbg("Cleaning up...",
                   self.__class__.__name__)
        for shutdown in self.cleanups:
            shutdown.cleanup()

    def signalhandler(self, signal, frame):
        """Handle signal
        """
        ##Set running to false for all
        self.recv.running = False
        self.__timedscheduler.running = False
        self.__scheduler.running = False

        self.cleanup()

        self.__timedscheduler.join(1.0)

        output.info("Exiting yapc...", self.__class__.__name__)
        sys.exit(0)


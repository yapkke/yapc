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
        if (eventname not in self.__processors):
            self.__processors[eventname] = []
        self.__processors[eventname].append(handler)

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
            output.vdbg("Dispatch next event",
                        self.__class__.__name__)
            event = self.__events.pop(0)
            try:
                for handler in self.__processors[event.name]:
                    if (not handler.processevent(event)):
                        break;
            except KeyError:
                #No handler, so pass
                output.warn("Event "+str(event.name)+" does not have handler",
                            self.__class__.__name__)
                

class server:
    """Daemon for yapc core

    Referred to Sander Marechal's simple unix/linux daemon in Python.

    @author ykk
    @date Oct 2010
    """
    def __init__(self, stdin='dev/null', stdout='dev/null',  stderr='dev/null'):
        """Initialize
        """
        ##File descriptors for daemon
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
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

    def daemonize(self):
        """Daemonize this class and run
        """
        #first fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed with error %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        #decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        #second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed with error %d (%s)\n"\
                                 % (e.errno, e.strerror))
            sys.exit(1)

        #redirect file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        #Run actual poll loop
        self.run()
        
    def run(self):
        """Main loop to run
        """
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
        for shutdown in self.scheduler.cleanups:
            shutdown.cleanup()
        output.info("Exiting yapc...", self.__class__.__name__)
        sys.exit(0)

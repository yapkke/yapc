##Interfaces for YAPC
#
# @author ykk
# @date Oct 2010
#
import os
import sys
import threading
import yapc.log.output as output

class event:
    """Base class for events

    @author ykk
    @date Oct 2010
    """
    ##Name
    name = None

class priv_callback(event):
    """Private callback event for class

    @author ykk
    @date Oct 2010
    """
    name = "Private Callback"
    def __init__(self, handler, magic):
        """Initialize
        
        @param handler object to handle event
        @param magic object to post this event with (e.g., another event)
        """
        ##Reference to handler
        self.handler = handler
        ##Reference to magic
        self.magic = magic
        
class component:
    """Base component for events
   
    Should only stores soft state used internally.
    I would argue that all hard state should be done by
    on systems like memcached. YAPC's framework allows 
    you to shoot yourself in the foot nonetheless.

    @author ykk
    @date Oct 2010
    """
    def processevent(self, event):
        """Dummy function to process event

        @param event reference to event
        @return True for continue, else stop
        """
        return True

class cleanup:
    """Base component that handles shutdown

    @author ykk
    @date Oct 2010
    """
    def cleanup(self):
        """Dummy function to cleanup
        """
        return

class static_callable:
    """Class to allow static function in Python
    """
    def __init__(self, function):
        """Initialize
        """
        self.__call__ = function

class async_task(threading.Thread):
    """Class that generates a thread for an async task

    Note that each object can only be run once 
    (i.e., you can only call start() once)

    @author ykk
    @date June 2011
    """
    def __init__(self):
        """Initialize
        """
        threading.Thread.__init__(self)
        ##Reference to yapc core
        self.server = None
        ##Reference to event to post at end of execution
        self.event = None
        ##Reference to executing state
        self.__running = None

    def is_running(self):
        """Return current running state of task

        @return current running task
        """
        return self.__running

    def set_end_event(self, server, event):
        """Set event to be sent when the task is done executing

        @param server yapc core
        @param event event to be posted
        """
        self.server = server
        self.event = event

    def run(self):
        """Main tasks for execution
        """
        self.__running = True
        self.task()
        self.__running = False
        if ((self.server != None) and (self.event != None)):
            self.server.post_event(self.event)

    def task (self):
        """Main function for task
        
        Dummy function that should be over written
        """
        pass

class daemon:
    """Class that can be daemonized
    
    Referred to Sander Marechal's simple unix/linux daemon in Python.

    @author ykk
    @date Feb 2011
    """
    def __init__(self, daemon=False,
                 stdin='dev/null', stdout='dev/null',  stderr='dev/null'):
        ##File descriptors for daemon
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        ##Run as daemon or not
        self.daemon = daemon

    def run(self):
        """Dummy run function
        """
        pass

    def start(self):
        """Start daemon or main thread
        """
        if (self.daemon):
            output.set_daemon_log()
            self.daemonize()
        else:
            self.run()

    def daemonize(self):
        """Daemonize class instance
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
                
        self.run()

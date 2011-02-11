##Interfaces for YAPC
#
# @author ykk
# @date Oct 2010
#
import os
import sys
import yapc.output as output

class event:
    """Base class for events

    @author ykk
    @date Oct 2010
    """
    ##Name
    name = None

class priv_event(event):
    """Private event for class

    @author ykk
    @date Oct 2010
    """
    name = "Private Event"
    def __init__(self, handler, event):
        """Initialize
        
        @param handler object to handle event
        @param event event
        """
        ##Reference to handler
        self.handler = handler
        ##Reference to event
        self.event = event
        
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

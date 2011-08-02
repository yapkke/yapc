##Terminal console utility
import yapc.interface as yapc
import yapc.output as output
import termios, fcntl, sys, os

class keyevent(yapc.event):
    """Event to send keystrokes

    @author ykk
    @date August 2011
    """
    name="Keyboard event"
    def __init__(self, keys):
        """Initialize
        """
        self.keys = keys

    def pop_char(self):
        """Get single character in keystokes list
        """
        if (len(self.keys) == 0):
            return None

        c = self.keys[0]
        self.keys = self.keys[1:]
        return c

class keylogger(yapc.cleanup, yapc.component):
    """Class to help with key logging

    @author ykk
    @date August 2011
    """
    def __init__(self, server, interval=0.2):
        """Initialize
        """

        ##Configure stdin
        self.fd = sys.stdin.fileno()
        
        self.oldterm = termios.tcgetattr(self.fd)
        newattr = termios.tcgetattr(self.fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(self.fd, termios.TCSANOW, newattr)
        
        self.oldflags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.oldflags | os.O_NONBLOCK)

        ##Register for events
        self.interval = interval
        self.server = server
        server.register_cleanup(self)
        server.post_event(yapc.priv_callback(self), 0) 

    def processevent(self, event):
        """Process event

        @param event event to process
        @return True
        """
        if (isinstance(event, yapc.priv_callback)):
            self.probe()
            self.server.post_event(yapc.priv_callback(self), self.interval) 

        return True

    def probe(self, maxlen=1000):
        """Probe for key strokes
        """
        try:
            keys = sys.stdin.read(maxlen)
            self.server.post_event(keyevent(keys))
        except IOError:
            pass

    def cleanup(self):
        """Cleanup
        """
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.oldterm)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.oldflags)

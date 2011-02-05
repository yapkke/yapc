## Communication primitives
#
# @author ykk
# @date Oct 2010
#
import select
import socket
import threading
import time
import yapc.output as output

BLOCKING = False

class sockmanager:
    """Class for managing sockets

    Includes buffer to store partially received message

    @author ykk
    @date Oct 2010
    """
    def __init__(self, maxlen=1):
        """Initialize with 
        * maximum length to receive at each time (default =1)
        """
        ##Maximum length to receive
        self.maxlen = maxlen
        ##Buffer for partially received messages
        self.buffer = ""

    def parsepacket(self):
        """Parse and process packets
        Dummy one simply consume and dump all content in buffer
        """
        self.processpacket(self.buffer)
        self.buffer = ""

    def receive(self, sock, recvthread):
        """Handle received
        """
        while (len(select.select([sock], [], [], 0)[0]) != 0):
            received = sock.recv(self.maxlen)
            if (len(received) == 0):
                recvthread.removeconnection(sock)
                return
            else:
                self.buffer += received
                self.parsepacket()

    def processpacket(self, packet):
        """Function to process packet

        (Dummy function that print packet verbatim)
        """
        output.dbg("Receive "+str(packet), self.__class__.__name__)

class receivethread(threading.Thread):
    """Receiver for messages

    Stores connections and poll them for messages
    
    @author ykk
    @date Oct 2010
    """
    def __init__(self):
        """Initialize
        """
        threading.Thread.__init__(self)
        ##Dictionary of sockets and managers
        self.__sockDictionary = {}
        ##List of sockets
        self.__sockets = []
        ##Sleep time
        self.timeout = 0.1
        ##Boolean for run
        self.running = True
        ##Set to daemon
        self.daemon = True

    def addconnection(self, sock, manager):
        """Add socket and manager
        """
        if (sock not in self.__sockets):
            self.__sockets.append(sock)
        self.__sockDictionary[sock] = manager
        output.dbg("Adding "+str(sock)+" to select list",
                   self.__class__.__name__)

    def removeconnection(self, sock):
        """Remove socket
        """
        if (sock in self.__sockDictionary):
            del self.__sockDictionary[sock]
        if (sock in self.__sockets):
            self.__sockets.remove(sock)
            output.dbg("Removing "+str(sock)+" to select list",
                       self.__class__.__name__)

    def run(self):
        """Main loop for polling receiving messages
        """
        inputready = []
        while self.running:
            #Poll if any socket
            if (len(self.__sockets) != 0):
                inputready, outputready, exceptready = \
                    select.select(self.__sockets, [], [], self.timeout)
            else:
                time.sleep(self.timeout)

            #Read any socket with data
            for readsock in inputready:
                sockmgr = self.__sockDictionary[readsock]
                sockmgr.receive(readsock, self)

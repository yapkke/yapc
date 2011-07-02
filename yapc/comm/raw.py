##Raw socket communication primitives
#
# @author ykk
# @date July 2011
#
import yapc.interface as yapc
import yapc.comm.core as comm
import yapc.log.output as output
import socket

class message(yapc.event):
    """Raw message event

    @author ykk
    @date July 2011
    """
    name = "Raw Message"
    def __init__(self, sock, msg):
        """Raw message event
        """
        ##Sock associated with
        self.sock = sock
        ##Message
        self.message = msg

    def reply(self, message):
        """Reply with message
        """
        self.sock.send(message)

class rawsocket(yapc.component, yapc.cleanup):
    """Class to create raw socket

    @author ykk
    @date July 2011
    """
    def __init__(self, server, intf, port=0, rawmgr=None):
        """Initialize

        Install client connection into receive thread
        """
        #Create client connection
        self.sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        self.sock.bind((intf,port))

        #Create socket manager
        self.mgr = rawmgr 
        if (self.mgr  == None):
            self.mgr = rawsocketmgr(server)
        server.recv.addconnection(self.sock, self.mgr)

        ##Cleanup
        server.register_cleanup(self)
        
    def cleanup(self):
        """Function to clean up server socket
        """
        self.sock.close()

    def send(self, message):
        """Send message

        @param message message to send
        """
        self.sock.send(message)

class rawsocketmgr(comm.sockmanager):
    """Class to receive raw messages from socket
    
    @author ykk
    @date July 2011
    """
    def __init__(self, scheduler=None, maxlen=2048):
        """Initialize
        """
        ##Reference to scheduler
        self.scheduler = scheduler
        ##Max length to receive
        self.maxlen = maxlen

    def receive(self, sock, recvthread):
        """Receive new connection
        """
        output.vvdbg("Receiving packet on raw socket "+str(sock),
                    self.__class__.__name__)        
        data = sock.recv(self.maxlen)
        self.scheduler.post_event(message(sock, data))


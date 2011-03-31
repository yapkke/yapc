##UDP communication primitives
#
# @author ykk
# @date Mar 2011
#
import yapc.interface as yapc
import yapc.comm.core as comm
import yapc.output as output
import socket
import sys

class message(yapc.event):
    """UDP message event

    @author ykk
    @date Mar 2011
    """
    name = "UDP Message"
    def __init__(self, sock, msg, addr):
        """UDP message event
        """
        ##Sock associated with
        self.sock = sock
        ##Message
        self.message = msg
        ##Address of peer
        self.address = addr

    def reply(self, message):
        """Reply with message
        """
        self.sock.sendto(message, self.address)

class udpserver(yapc.component, yapc.cleanup):
    """Class to create UDP server socket

    @author ykk
    @date Mar 2011
    """
    def __init__(self, server, port,
                 host='', udpservermgr=None):
        """Initialize

        Bind core scheduler and receive thread
        Install server connection into receive thread
        """
        #Create server connection
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((host, port))
        output.info("Binding UDP to "+str(host)+":"+str(port),
                    self.__class__.__name__)

        #Create server manager
        self.udpservermgr = udpservermgr 
        if (self.udpservermgr  == None):
            self.udpservermgr = udpsocket(server)
        server.recv.addconnection(self.server, self.udpservermgr)

        ##Cleanup
        server.register_cleanup(self)
        
    def cleanup(self):
        """Function to clean up server socket
        """
        self.server.close()

class udpclient(yapc.component, yapc.cleanup):
    """Class to create UDP client socket

    @author ykk
    @date Mar 2011
    """
    def __init__(self, server, udpclientmgr=None):
        """Initialize

        Install client connection into receive thread
        """
        #Create client connection
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #Create server manager
        self.udpclientmgr = udpclientmgr 
        if (self.udpclientmgr  == None):
            self.udpclientmgr = udpsocket(server)
        server.recv.addconnection(self.sock, self.udpclientmgr)

        ##Cleanup
        server.register_cleanup(self)
        
    def cleanup(self):
        """Function to clean up server socket
        """
        self.sock.close()

    def send(self, message, addr):
        """Send message

        @param message message to send
        @param address (host, port)
        """
        self.sock.sendto(message, addr)

class udpsocket(comm.sockmanager):
    """Class to receive UDP packets from socket

    @author ykk
    @date Mar 2011
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
        output.vvdbg("Receiving packet on UDP socket "+str(sock),
                    self.__class__.__name__)        
        data, addr = sock.recvfrom(self.maxlen)
        self.scheduler.post_event(message(sock, data, addr))

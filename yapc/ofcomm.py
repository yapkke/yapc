##OpenFlow communication primitives
#
# @author ykk
# @date Oct 2010
#
import yapc.interface as yapc
import yapc.comm as comm
import yapc.pyopenflow as pyopenflow
import yapc.output as output
import socket
import sys

class message(yapc.event):
    """OpenFlow message event

    @author ykk
    @date Oct 2010
    """
    name = "OpenFlow Message"
    def __init__(self, sock, msg):
        """OpenFlow message event
        """
        ##Header
        self.header = pyopenflow.ofp_header()
        self.header.unpack(msg)
        ##Connection message is received from
        self.sock = sock
        ##Message
        self.message = msg

class connection:
    """Class to manage OpenFlow connection

    @author ykk
    @date Oct 2010
    """
    def __init__(self, sock):
        """Initialize
        """
        ##Status of handshake
        self.handshake = False
        ##Reference to sock
        self.sock = sock
        ##Datapath id of connection
        self.dpid = None

    def __del__(self):
        """Destructor
        """
        self.sock.close()

    def dohandshake(self, msg):
        """Function to carry out handshake

        Switch (hello) => hello + feature request
        Switch (feature reply) => DONE
        """
        if (msg.header.type == pyopenflow.OFPT_HELLO):
            sendmsg = pyopenflow.ofp_hello()
            self.send(sendmsg.pack())
            sendmsg = pyopenflow.ofp_header()
            sendmsg.type = pyopenflow.OFPT_FEATURES_REQUEST
            self.send(sendmsg.pack())

        elif (msg.header.type == pyopenflow.OFPT_FEATURES_REPLY):
            switch_feature = pyopenflow.ofp_switch_features()
            switch_feature.unpack(msg.message)
            self.dpid = switch_feature.datapath_id
            output.info("Connected to switch %x" % self.dpid,
                        self.__class__.__name__)
            self.handshake = True

        else:
            output.warn("Handshake should not handle message type"+\
                            ofp_type[msg.header.type],
                        self.__class__.__name__)

    def replyecho(self, msg):
        """Handle echo request
        """
        sendmsg = pyopenflow.ofp_header()
        sendmsg.type = pyopenflow.OFPT_ECHO_REPLY
        sendmsg.xid = msg.header.xid
        self.send(sendmsg.pack())

    def send(self, msg):
        """Send OpenFlow message
        """
        header = pyopenflow.ofp_header()
        if (len(msg) < len(header)):
            output.warn("Cannot send OpenFlow of length "+str(len(msg)))
        else:
            remain = header.unpack(msg)
            header.length = len(msg)
            output.vdbg("Send message "+header.show().strip().replace("\n",";"),
                        self.__class__.__name__)
            try:
                self.sock.send(header.pack()+remain)
            except socket.error:
                output.warn("Broken pipe, message not sent")

class connections:
    """Class to manage OpenFlow connections

    @author ykk
    @date Oct 2010
    """
    def __init__(self):
        """Initialize
        """
        ##Dictionary of connections
        self.db = {}
        
    def add(self, sock):
        """Add connection
        """
        self.db[sock] = connection(sock)

    def remove(self, sock):
        """Delete connection
        """
        if (sock in self.db):
            self.db.pop(sock)
            output.dbg("Remove stale OpenFlow connection "+str(sock),
                       self.__class__.__name__)

class ofsockmanager(comm.sockmanager):
    """Class to manage OpenFlow 

    @author ykk
    @date Oct 2010
    """
    def __init__(self, sock, scheduler):
        """Initialize
        """
        comm.sockmanager.__init__(self, sock, scheduler)
        ##Header object
        self.__header = pyopenflow.ofp_header()
       
    def parsepacket(self):
        """Parse and process packets
        """
        if len(self.buffer) >= len(self.__header):
            self.__header.unpack(self.buffer)
            if (len(self.buffer) == self.__header.length):
                self.processpacket(self.buffer)
                self.buffer = ""

    def processpacket(self, packet):
        """Function to process packet
        
        (Dummy function that print packet verbatim)
        """
        output.vdbg("Receive OpenFlow packet of "+\
                        self.__header.show().strip().replace("\n",";"),
                   self.__class__.__name__)
        msg = message(self.sock, packet)
        self.scheduler.postevent(msg)

class ofserver(yapc.component, yapc.cleanup):
    """Class to create OpenFlow server socket

    @author ykk
    @date Oct 2010
    """
    def __init__(self, server,
                 port=6633, host='', backlog=10, ofservermgr=None):
        """Initialize

        Bind core scheduler and receive thread
        Install server connection into receive thread
        """
        #Create server connection
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        output.info("Binding OpenFlow to "+str(host)+":"+str(port),
                    self.__class__.__name__)
        self.server.listen(backlog)
        #Create server manager
        self.ofservermgr = ofservermgr 
        if (self.ofservermgr  == None):
            self.ofservermgr = ofserversocket()

        #Bind
        self.ofservermgr.scheduler = server.scheduler
        server.recv.addconnection(self.server, self.ofservermgr)

        ##OpenFlow connections
        self.connections = connections()
        server.scheduler.registereventhandler(message.name,
                                              self)
        server.scheduler.registereventhandler(comm.event.name,
                                              self)

    def processevent(self, event):
        """Event handler

        Process basic OpenFlow messages:
        1) Handshake for new connections
        2) Replies for echo request

        @param event event to handle
        """
        if (isinstance(event, comm.event)):
            #Remove stale connection
            if (event.event == comm.event.SOCK_CLOSE):
                self.connections.remove(event.sock)
                
        elif (isinstance(event, message)):
            #OpenFlow connection
            if (event.sock not in self.connections.db):
                self.connections.add(event.sock)

            if isinstance(event, message):
                if (not self.connections.db[event.sock].handshake):
                    #Handshake
                    self.connections.db[event.sock].dohandshake(event)
                elif (event.header.type == pyopenflow.OFPT_ECHO_REQUEST):
                    #Echo replies
                    self.connections.db[event.sock].replyecho(event)
                    
        return True

    def cleanup(self):
        """Function to clean up server socket
        """
        self.server.close()

        
class ofserversocket(comm.sockmanager):
    """Class to accept OpenFlow connections

    @author ykk
    @date Oct 2010
    """
    def __init__(self, scheduler=None):
        """Initialize
        """
        self.scheduler = scheduler

    def receive(self, sock, recvthread):
        """Receive new connection
        """
        client, address = sock.accept()
        if (not comm.BLOCKING):
            client.setblocking(0)
        recvthread.addconnection(client, ofsockmanager(client, self.scheduler))
        self.scheduler.postevent(comm.event(client,
                                            comm.event.SOCK_OPEN))
        output.dbg("Connection to "+str(address)+" added", self.__class__.__name__)

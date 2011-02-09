##JSON communication primitives
#
# @author ykk
# @date Oct 2010
#
import yapc.interface as yapc
import yapc.comm as comm
import yapc.output as output
import socket
import simplejson
import os
import stat

class message(yapc.event):
    """JSON message event

    @author ykk
    @date Oct 2010
    """
    name = "JSON Message"
    def __init__(self, sock, msg):
        """JSON message event
        """
        ##Socket message is received from
        self.sock = sock
        ##Message
        self.message = simplejson.loads(msg)

class client:
    """JSON client connection

    @author ykk
    @date Oct 2010
    """
    def __init__(self, file="json.sock"):
        """Initialize
        """
        ##Reference to socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(file)

    def __del__(self):
        """Destructor
        """
        #self.sock.close()
        pass

class connection:
    """Class to manage JSON connection

    @author ykk
    @date Oct 2010
    """
    def __init__(self, sock):
        """Initialize
        """
        ##Reference to sock
        self.sock = sock

    def __del__(self):
        """Destructor
        """
        self.sock.close()

    def send(self, msg):
        """Send dictionary as JSON message
        """
        self.sock.send(simplejson.dumps(msg))
        output.dbg("Send message "+simplejson.dumps(msg),
                   self.__class__.__name__)

    def getpeerid(self):
        """Get peer pid, uid and gid of socket
        """
        SO_PEERCRED = 17
        pid, uid, gid = struct.unpack('3i', self.sock.getsockopt(
            socket.SOL_SOCKET, SO_PEERCRED, struct.calcsize('3i')))
        
        return (pid, uid, gid)
            
class connections:
    """Class to manage JSON connections

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

class jsonsockmanager(comm.sockmanager):
    """Class to manage JSON connection

    @author ykk
    @date Oct 2010
    """
    def __init__(self, sock, scheduler):
        """Initialize
        """
        comm.sockmanager.__init__(self, sock, scheduler)

    def parsepacket(self):
        """Parse and process packets
        """
        try:
            simplejson.loads(self.buffer)
            self.processpacket(self.buffer)
            self.buffer = ""
        except ValueError:
            pass

    def processpacket(self, packet):
        """Function to process packet
        """
        output.dbg("Receive JSON packet of "+packet, self.__class__.__name__)
        msg = message(self.sock, packet)
        self.scheduler.postevent(msg)

class jsonserver(yapc.cleanup):
    """Class to create JSON server socket

    @author ykk
    @date Oct 2010
    """
    def __init__(self, server,
                 file='json.sock', backlog=10, jsonservermgr=None,
                 forcebind=True):
        """Initialize

        * Install server connection into receive thread
        * Register scheduler for processing message events
        """
        #Reference to socket file
        self.__file = file
        #Create server connection
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.server.bind(file)
            output.info("Binding to "+file, self.__class__.__name__)
        except socket.error:
            if (forcebind):
                os.remove(file)
                self.server.bind(file)
                output.warn("Force binding to "+file, self.__class__.__name__)
            else:
                raise

        self.server.listen(backlog)
        os.chmod(file, stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)
        #Create server manager
        self.jsonservermgr = jsonservermgr
        if (self.jsonservermgr  == None):
            self.jsonservermgr = jsonserversocket()

        #Bind to scheduler
        self.jsonservermgr.scheduler = server.scheduler
        server.recv.addconnection(self.server, self.jsonservermgr)
        server.scheduler.registercleanup(self)

        ##OpenFlow connections
        self.connections = connections()
        server.scheduler.registereventhandler(message.name,
                                              self)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        """
        if (event.sock not in self.connections.db):
            self.connections.add(event.sock)

        return True

    def __del__(self):
        """Destructor, thus cleanup
        """
        self.cleanup()
        
    def cleanup(self):
        """Function to clean up server socket
        """
        self.server.close()
        os.remove(self.__file)

class jsonserversocket(comm.sockmanager):
    """Class to accept JSON connections

    @author ykk
    @date Oct 2010
    """
    def __init__(self, scheduler=None):
        """Initialize
        """
        ##Reference to scheduler
        self.scheduler = scheduler

    def receive(self, sock, recvthread):
        """Receive new connection
        """
        client, address = sock.accept()
        if (not comm.BLOCKING):
            client.setblocking(0)
        recvthread.addconnection(client, jsonsockmanager(client, self.scheduler))
        self.scheduler.postevent(comm.event(client,
                                            comm.event.SOCK_OPEN))
        output.dbg("Connection to "+str(address)+" added", self.__class__.__name__)

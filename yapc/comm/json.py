##JSON communication primitives
#
# @author ykk
# @date Oct 2010
#
import yapc.interface as yapc
import yapc.comm.core as comm
import yapc.log.output as output
import socket
import simplejson
import os
import stat
import select

SOCK_NAME = "json.sock"

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

    def reply(self, msg):
        """Reply with a message
        """
        self.sock.send(simplejson.dumps(msg))

class client:
    """JSON client connection

    @author ykk
    @date Oct 2010
    """
    def __init__(self, file=SOCK_NAME):
        """Initialize
        """
        ##Reference to socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(file)
        
    def recv(self, maxlen=1024, timeout=10):
        """Receive data
        """
        ready = select.select([self.sock], [], [], timeout)
        if ready[0]:
            return self.sock.recv(maxlen)
        else:
            return "{}"
        
    def __del__(self):
        """Destructor
        """
        self.sock.close()
        
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
        try:
            self.sock.send(simplejson.dumps(msg))
            output.dbg("Send message "+simplejson.dumps(msg),
                       self.__class__.__name__)
        except socket.error:
            output.warn(str(self.sock)+" is broken, message is dropped!",
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

    def remove(self, sock):
        """Delete connection
        """
        if (sock in self.db):
            self.db.pop(sock)
            output.dbg("Remove stale JSON connection "+str(sock),
                       self.__class__.__name__)

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
        self.scheduler.post_event(msg)

class jsonserver(yapc.cleanup):
    """Class to create JSON server socket

    @author ykk
    @date Oct 2010
    """
    def __init__(self, server,
                 file=SOCK_NAME, backlog=10, jsonservermgr=None,
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
        self.jsonservermgr.scheduler = server
        server.recv.addconnection(self.server, self.jsonservermgr)
        server.register_cleanup(self)

        ##OpenFlow connections
        self.connections = connections()
        server.register_event_handler(message.name,
                                      self)
        server.register_event_handler(comm.event.name,
                                      self)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        """
        if (isinstance(event, comm.event)):
            #Remove stale connection
            if (event.event == comm.event.SOCK_CLOSE):
                self.connections.remove(event.sock)
                
        elif (isinstance(event, message)):
            #JSON connection
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
        self.scheduler.post_event(comm.event(client,
                                            comm.event.SOCK_OPEN))
        output.dbg("Connection to "+str(address)+" added", self.__class__.__name__)

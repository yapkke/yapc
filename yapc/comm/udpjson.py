##UDP with JSON message
#
# @author ykk
# @date Aug 2011
#
import yapc.comm.udp as udp
import yapc.comm.basejson as bjson
import simplejson

SOCK_PORT = 2605

class message(udp.message):
    """UDP message with JSON
    
    @author ykk
    @date Aug 2011
    """
    name = "JSON UDP Message"
    def __init__(self, sock, msg, addr):
        """JSON UDP message event
        """
        udp.message.__init__(self, sock, msg, addr)
        bjson.message.__init__(self, msg)

    def reply(self, message):
        """Reply with message
        """
        udp.message.reply(simplejson.dumps(message))

class jsonudpserver(udp.udpserver):
    """Class to create UDP server socket that handles JSON
    
    @author ykk
    @date Aug 2011
    """
    def __init__(self, server, port,
                 host='', udpservermgr=None):
        """Initialize

        Bind core scheduler and receive thread
        Install server connection into receive thread
        """
        if (udpservermgr == None):
            udp.udpserver.__init__(self, server, port, host, jsonudpsocket(server))
        else:
            udp.udpserver.__init__(self, server, port, host, udpservermgr)

class jsonudpclient(udp.udpclient):
    """Class to create JSON UDP client socket

    @author ykk
    @date Aug 2011
    """
    def __init__(self, server, udpclientmgr=None):
        """Initialize

        Install client connection into receive thread
        """
        if (udpclientmgr == None):
            udp.udpserver.__init__(self, server, jsonudpsocket(server))
        else:
            udp.udpserver.__init__(self, server, udpclientmgr)

    def send(self, message, addr):
        """Send message

        @param message message to send
        @param address (host, port)
        """
        self.sock.sendto(simplejson.dumps(message), addr)
                    
class jsonudpsocket(udp.udpsocket):
    """Class to receive JSON UDP packets from socket
    
    @author ykk
    @date Aug 2011
    """
    def receive(self, sock, recvthread):
        """Receive new connection
        """
        output.vvdbg("Receiving packet on JSON UDP socket "+str(sock),
                    self.__class__.__name__)        
        data, addr = sock.recvfrom(self.maxlen)
        self.scheduler.post_event(message(sock, data, addr))

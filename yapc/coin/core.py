##COIN core
#
# Client-side OpenFlow Interface for Networking
#
# @author ykk
# @date Oct 2010
#
import yapc.interface as yapc
import yapc.ofcomm as ofcomm
import yapc.jsoncomm as jsoncomm
import yapc.output as output
import yapc.pyopenflow as pyopenflow
import yapc.commands as cmd
import netifaces

SOCK_NAME = "/etc/coin.sock"
IFCONFIG = "ifconfig"

class interfacemgr:
    """Interface manager class to manage interfaces

    @author ykk
    @date Feb 2011
    """
    def __init__(self):
        """Initialize
        """
        pass

    def interfaces(self):
        """Return interfaces
        @return interface names
        """
        return netifaces.interfaces()

    def ifaddresses(self, intf=None):
        """Return addresses for specified interface or all interfaces
        
        @param intf interface
        @return addresses or dictionary of addresses
        """
        if (intf == None):
            result = {}
            for i in self.interfaces():
                result[i] = netifaces.ifaddresses(i)
            return result
        else:
            return netifaces.ifaddresses(intf)

    def ethernet_ipv4_addresses(self, intf=None):
        """Return Ethernet + IPv4 addresses for specified interface or all interfaces
        
        @param intf interface
        @return Ethernet and IPv4  addresses
        """
        ifaddr = self.ifaddresses(intf)
        if (intf == None):
            result = {}
            for i,addr in ifaddr.items():
                if (netifaces.AF_PACKET in addr):
                    result[i] = self.__get_ethernet_ipv4_addr(addr)
        else:
            return self.__get_ethernet_ipv4_addr(ifaddr)
        return result
    
    def __get_ethernet_ipv4_addr(self, addr):
        """Extract Ethernet and IPv4 addresses
        
        @param addr addresses of a single interface
        @return dictionary of Ethernet and IPv4 addresses, None otherwise
        """
        result = {}
        if (netifaces.AF_PACKET in addr):
            result[netifaces.AF_PACKET] = addr[netifaces.AF_PACKET]
            if (netifaces.AF_INET in addr):
                result[netifaces.AF_INET] = addr[netifaces.AF_INET]
            return result
        else:
            return None

    def set_ipv4_addr(self, intf, addr, netmask=None):
        """Set IPv4 address
        
        @param intf interface name
        @param addr IPv4 address string
        @param netmask network mask string
        """
        c = IFCONFIG+" "+intf+" "+addr
        if (netmask != None):
            c += " netmask "+netmask
        cmd.run_cmd(c, self.__class__.__name__)

class server(yapc.component):
    """Class to handle connections and configuration for COIN

    @author ykk
    @date Oct 2010
    """
    def __init__(self):
        """Initialize
        """
        ##OpenFlow connections
        self.connections = ofcomm.connections()
        ##JSON connections
        self.jsonconnections = jsoncomm.connections()
        ##Global COIN dictionary
        self.config = {}
        self.config["mode"] = None
        ##Interface Manager
        self.ifmgr = interfacemgr()
        
    def set_config(self, name, val):
        """Set config

        @param name name of config
        @param val value to set config to
        """
        self.config[name] = val

    def set_config_if_none(self, name, val):
        """Set config

        @param name name of config
        @param val value to set config to
        """
        if (name not in self.config):
            self.set_config(name, val)

    def get_config(self, name):
        """Get config

        @param name name of config
        @return config value else None
        """
        try:
            return self.config[name]
        except KeyError:
            return None

    def processevent(self, event):
        """Process OpenFlow and JSON messages

        @param event event to handle
        @return True
        """
        if isinstance(event, ofcomm.message):
            #OpenFlow messages
            self.__processof(event)
        elif isinstance(event, jsoncomm.message):
            #JSON messages
            self.__processjson(event)
            
        return True

    def __processof(self, event):
        """Process basic OpenFlow messages:
        1) Handshake for new connections
        2) Replies for echo request
        3) Print error messages
        
        @param event yapc.ofcomm.message event
        """
        if (event.sock not in self.connections.db):
            self.connections.add(event.sock)
            
        if (not self.connections.db[event.sock].handshake):
            #Handshake
            self.connections.db[event.sock].dohandshake(event)
        elif (event.header.type == pyopenflow.OFPT_ECHO_REQUEST):
            #Echo replies
            self.connections.db[event.sock].replyecho(event)
        elif (event.header.type == pyopenflow.OFPT_ERROR):
            #Error
            oem = pyopenflow.ofp_error_msg()
            oem.unpack(event.message)
            output.warn("Error of type "+str(oem.type)+" code "+str(oem.code),
                        self.__class__.__name__)
        else:
            output.dbg("Receive message "+event.header.show().strip().replace("\n",";"),
                       self.__class__.__name__)

    def __processjson(self, event):
        """Process basic JSON messages
        
        @param event yapc.jsoncomm.message event
        """
        if (event.sock not in self.jsonconnections.db):
            self.jsonconnections.add(event.sock)
        
        if (event.message["type"] == "coin" and
            event.message["subtype"] == "global"):
            reply = self.__processglobal(event)
            if (reply != None):
                self.jsonconnections.db[event.sock].send(reply)
        else:
            output.dbg("Receive JSON message "+simplejson.dumps(event.message),
                       self.__class__.__name__)

    def __processglobal(self, event):
        """Process mode related JSON messages
        
        @param event yapc.jsoncomm.message event
        """
        reply = {}
        reply["type"] = "coin"
        
        if (event.message["command"] == "get_mode"):
            reply["subtype"] = "mode"
            reply["mode"] = str(self.get_config("mode"))
        elif (event.message["command"] == "get_interfaces"):
            reply["subtype"] = "interfaces"
            reply["interfaces"] = self.ifmgr.ethernet_ipv4_addresses()
        else:
            output.dbg("Receive message "+str(event.message),
                       self.__class__.__name__)
            return None

        return reply

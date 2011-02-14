##COIN core
#
# Client-side OpenFlow Interface for Networking
#
# @author ykk
# @date Oct 2010
#
import yapc.interface as yapc
import yapc.events.openflow as ofevents
import yapc.jsoncomm as jsoncomm
import yapc.output as output
import yapc.commands as cmd
import yapc.local.netintf as loifaces
import yapc.coin.nat as cnat
import yapc.coin.ovs as ovs
import simplejson

SOCK_NAME = "/etc/coin.sock"

class server(yapc.component):
    """Class to handle connections and configuration for COIN

    @author ykk
    @date Oct 2010
    """
    def __init__(self, server, ofconn, jsonconn):
        """Initialize

        @param server yapc core server/scheduler
        """
        ##OpenFlow connections
        self.ofconnections = ofconn
        ##JSON connections
        self.jsonconnections = jsonconn
        ##Global COIN dictionary
        self.config = {}
        self.config["mode"] = None
        ##Interface Manager
        self.ifmgr = loifaces.interfacemgr(server)
        ##NAT Manager
        self.natmgr = cnat.natmgr(self.ifmgr)
        ##Reference to switch fabric
        self.switch = None

        server.register_event_handler(ofevents.error.name,
                                      self)
        server.register_event_handler(jsoncomm.message.name,
                                      self)

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
        if isinstance(event, ofevents.error):
            #OpenFlow error
            output.warn("Error of type "+str(event.error.type)+\
                            " code "+str(event.error.code),
                        self.__class__.__name__)
        elif isinstance(event, jsoncomm.message):
            #JSON messages
            self.__processjson(event)
            
        return True

    def __processjson(self, event):
        """Process basic JSON messages
        
        @param event yapc.jsoncomm.message event
        """        
        if (event.message["type"] == "coin" and
            event.message["subtype"] == "global"):
            reply = self.__processglobal(event)
            if (reply != None):
                self.jsonconnections.db[event.sock].send(reply)
        elif (event.message["type"] == "coin" and
            event.message["subtype"] == "nat"):
            reply = self.__processnat(event)
            if (reply != None):
                self.jsonconnections.db[event.sock].send(reply)
        else:
            output.dbg("Receive JSON message "+simplejson.dumps(event.message),
                       self.__class__.__name__)

    def __processnat(self, event):
        """Process NAT related JSON messages
        
        @param event yapc.jsoncomm.message event
        """
        reply = {}
        reply["type"] = "coin"
        reply["subtype"] = "nat"

        if (event.message["command"] == "create_nat"):
            nat = self.natmgr.add(event.message["name"])
            self.switch.datapaths[ovs.COIN_DP_NAME].add_if(nat.client_intf)
        else:
            output.dbg("Receive message "+str(event.message),
                       self.__class__.__name__)
            return None

        return reply

    def __processglobal(self, event):
        """Process mode related JSON messages
        
        @param event yapc.jsoncomm.message event
        """
        reply = {}
        reply["type"] = "coin"
        
        if (event.message["command"] == "get_mode"):
            reply["subtype"] = "mode"
            reply["mode"] = str(self.get_config("mode"))
        elif (event.message["command"] == "get_eth_interfaces"):
            reply["subtype"] = "interfaces"
            reply["interfaces"] = self.ifmgr.ethernet_ipv4_addresses()
        else:
            output.dbg("Receive message "+str(event.message),
                       self.__class__.__name__)
            return None

        return reply

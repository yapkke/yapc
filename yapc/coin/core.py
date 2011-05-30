##COIN core
#
# Client-side OpenFlow Interface for Networking
#
# @author ykk
# @date Oct 2010
#
import yapc.interface as yapc
import yapc.events.openflow as ofevents
import yapc.comm.json as jsoncomm
import yapc.log.output as output
import yapc.commands as cmd
import yapc.local.netintf as loifaces
import yapc.coin.local as coinlo
import yapc.coin.ovs as ovs
import yapc.forwarding.default as default
import yapc.forwarding.flows as flows
import yapc.util.openflow as ofutil
import yapc.pyopenflow as pyof
import simplejson

SOCK_NAME = "/etc/coin.sock"

class coin_server(yapc.component):
    """Class to handle connections and configuration for COIN

    @author ykk
    @date Oct 2010
    """
    def __init__(self, server, ofconn, jsonconn):
        """Initialize

        @param server yapc core server/scheduler
        @param ofconn OpenFlow connections
        @param jsonconn JSON connections
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
        ##Local interface Manager
        self.loifmgr = coinlo.loifmgr(self.ifmgr)
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
            event.message["subtype"] == "loif"):
            reply = self.__processnat(event)
            if (reply != None):
                self.jsonconnections.db[event.sock].send(reply)
        else:
            output.dbg("Receive JSON message "+simplejson.dumps(event.message),
                       self.__class__.__name__)

    def __processloif(self, event):
        """Process local interfaces related JSON messages
        
        @param event yapc.jsoncomm.message event
        """
        reply = {}
        reply["type"] = "coin"
        reply["subtype"] = "loif"

        if (event.message["command"] == "create_lo_intf"):
            self.add_loif(event.message["name"])
        else:
            output.dbg("Receive message "+str(event.message),
                       self.__class__.__name__)
            return None

        return reply

    def add_loif(self, name):
        """Add local interface
        
        @param name name of interface pair
        @return interface pair
        """
        loif = self.loifmgr.add(name)
        self.switch.datapaths[ovs.COIN_DP_NAME].add_if(loif.switch_intf)
        return loif

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

    def add_interfaces(self, interfaces):
        """Add interfaces
        
        @param interfaces list of interfaces
        """
        for i in interfaces:
            self.switch.add_if(i)

class default_entries(default.default_entries):
    def __init__(self, server, ofconn):
        """Initialize
        
        @param server yapc core
        @param ofconn refrence to connections
        """
        default.default_entries.__init__(self, server, ofconn)

        self.add(flows.all_entry(flows.flow_entry.DROP,
                                 ofutil.PRIORITY['LOWEST'],
                                 pyof.OFP_FLOW_PERMANENT,
                                 pyof.OFP_FLOW_PERMANENT))
        self.add_perm(flows.tcp_entry(action=flows.flow_entry.GET,
                                      priority=ofutil.PRIORITY['LOWER']))
        self.add_perm(flows.udp_entry(action=flows.flow_entry.GET,
                                      priority=ofutil.PRIORITY['LOWER']))
        self.add_perm(flows.icmp_entry(action=flows.flow_entry.GET,
                                       priority=ofutil.PRIORITY['LOWER']))

class nat(coin_server):
    """Class to handle connections and configuration for COIN in NAT mode

    @author ykk
    @date May 2011
    """
    def __init__(self, server, ofconn, jsonconn):
        """Initialize

        @param server yapc core server/scheduler
        @param ofconn OpenFlow connections
        @param jsonconn JSON connections
        """
        coin_server.__init__(self, server, ofconn, jsonconn)
        ##Reference to local interface
        self.loif = None
        ##Reference to wifi manager
        self.wifimgr = loifaces.wifi_mgr()

    def setup(self, interfaces, networks,
              inner_addr='192.168.0.1'):
        """Add interfaces
        
        @param interfaces list of interfaces
        """
        #Set up interfaces
        self.loif = self.add_loif("local")
        self.add_interfaces(interfaces)

        #Get IP addresses on the interfaces
        self.ifmgr.set_ipv4_addr(self.loif.client_intf, inner_addr)
        #for i in range(0, len(networks)):
        #    self.ifmgr.up(interfaces[i])
        #    self.wifimgr.associate(interfaces[i], networks[i])
        #   self.ifmgr.invoke_dhcp(interfaces[i])
        

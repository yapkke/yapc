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
import yapc.util.parse as pu
import yapc.pyopenflow as pyof
import simplejson

SOCK_NAME = "/etc/coin.sock"

class component(yapc.component):
    """Base class for COIN's component
   
    @author ykk
    @date Jun 2011
    """
    def __init__(self, ofconn, coin=None):
        """Initialize

        @param conn reference to connections
        """
        ##Reference to connections
        self.conn = ofconn
        ##Reference to COIN
        self.coin = coin

    def get_conn(self):
        """Get connection

        @return the one and only connection to send messages (None otherwise)
        """
        if (len(self.conn.db) > 1):
            output.warn("More than one connection to COIN!",
                        self.__class__.__name__)

        for s,c in self.conn.db.items():
            return c

        return None

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
        self.add_perm_output(flows.tcp_entry(priority=ofutil.PRIORITY['LOWER']),
                             max_len=65535)
        self.add_perm_output(flows.udp_entry(priority=ofutil.PRIORITY['LOWER']),
                             max_len=65535)
        self.add_perm_output(flows.icmp_entry(priority=ofutil.PRIORITY['LOWER']),
                             max_len=65535)
        self.add_perm_output(flows.arp_entry(priority=ofutil.PRIORITY['HIGH']),
                             max_len=65535)

class coin_server(yapc.component):
    """Class to handle connections and configuration for COIN

    @author ykk
    @date Oct 2010
    """
    def __init__(self, server, ofconn, jsonconn, regEvent=True):
        """Initialize

        @param server yapc core server/scheduler
        @param ofconn OpenFlow connections
        @param jsonconn JSON connections
        """
        ##Reference to core
        self.server = server
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
       ##Reference to wifi manager
        self.wifimgr = loifaces.wifi_mgr()        
        ##Reference to default entries
        self.default = default_entries(server, ofconn)
        
        ##Reference to switch fabric
        self.switch = None

        if (regEvent):
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
            reply = self._processglobal(event)
            if (reply != None):
                self.jsonconnections.db[event.sock].send(reply)
        elif (event.message["type"] == "coin" and
            event.message["subtype"] == "loif"):
            reply = self.__processloif(event)
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

    def get_if_route(self, intf=None, mif=None):
        """Get route for interface
        
        @param intf interface name
        @param mif mirror interface name (else will resolve)
        """
        if (intf== None and mif == None):
            return None

        if (mif == None):
            mif = self.mirror[intf].client_intf

        self.ifmgr.query_route()
        gw = self.ifmgr.get_gateways([mif])
        if (len(gw) == 0):
            return None
        else:
            return gw[0]

    def get_ip_mac(self, ip, iface):
        """Get mac address of IP

        @param ip IP address to get mac for
        """
        self.ifmgr.arp_probe(iface, ip)
        self.ifmgr.query_arp()
        return self.ifmgr.get_arp(ip)
 
    def add_loif(self, name):
        """Add local interface
        
        @param name name of interface pair
        @return interface pair
        """
        loif = self.loifmgr.add(name)
        self.switch.datapaths[ovs.COIN_DP_NAME].add_if(loif.switch_intf)
        return loif

    def _processglobal(self, event):
        """Process mode related JSON messages
        
        @param event yapc.jsoncomm.message event
        """
        reply = {}
        reply["type"] = "coin"
        
        if (event.message["command"] == "get_all_config"):
            reply["subtype"] = "config"
            reply["value"] = self.config
        elif (event.message["command"] == "get_config"):
            reply["subtype"] = "config"
            reply["value"] = self.get_config(event.message["name"])
        elif (event.message["command"] == "set_config"):
            reply["subtype"] = "config"
            reply["previous value"] = self.get_config(event.message["name"])
            self.set_config(event.message["name"], event.message["value"])
            reply["current value"] = str(self.get_config(event.message["name"]))
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


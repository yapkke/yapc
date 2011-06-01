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
        elif isinstance(event, yapc.priv_callback):
            if (event.magic["type"] == "route"):
                self.__route_check(event.magic)
            else:
                self.__arp_check(event.magic)
            
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
        elif (event.message["command"] == "dhclient"):
            reply["dhclient result"] = self.dhclient_mirror(event.message["name"])
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
 
    def __arp_check(self, o):
        """Check ARP
        
        @param o arp check object (dictionary)
        """
        mac = self.get_ip_mac(o["ip"], o["if"])
        if (mac == None):
            o["tried"] += 1
            if (o["tried"] < 5):
                rc = yapc.priv_callback(self, o)
                self.server.post_event(rc, 1)
        else:
            self.gw_mac[o["ip"]] = mac.mac
            output.info("ARP of "+o["ip"]+" is "+str(mac.mac),
                        self.__class__.__name__)

    def __route_check(self, o):
        """Check route
        
        @param o route check object (dictionary)
        """
        gw = self.get_if_route(mif=o["mif"])
        if (gw == None):
            o["tried"] += 1
            if (o["tried"] < 5):
                rc = yapc.priv_callback(self, o)
                self.server.post_event(rc, 1)
        else:
            self.gateway[o["if"]] = gw
            output.info("Gateway of "+o["if"]+" is "+gw,
                        self.__class__.__name__)
            #Call for ARP
            rc = yapc.priv_callback(self, 
                                    {"type":"arp","tried":0, "ip":gw, "if":o["mif"]})
            self.server.post_event(rc, 0)
            
    def dhclient_mirror(self, intf):
        """Perform dhclient on mirror interface
       
        @param intf interface (primary)
        """
        mif = self.mirror[intf].client_intf
        self.ifmgr.invoke_dhcp(mif)
        rc = yapc.priv_callback(self, 
                                {"type":"route","tried":0, "if":intf, "mif":mif})
        self.server.post_event(rc, 0)

        return "executed"

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


class nat(coin_server):
    """Class to handle connections and configuration for COIN in NAT mode

    Mirror interfaces for DHCP and ARP.

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
        ##Mode
        self.config["mode"] = "Multi-Homed (NATed)"
        ##Reference to local interface
        self.loif = None
        ##Mirror interfaces (indexed by primary interface)
        self.mirror = {}
        ##Record of gateway (indexed by primary interface)
        self.gateway = {}
        ##Record of gateway mac (indexed by primary interface)
        self.gw_mac = {}

    def setup(self, interfaces, inner_addr='192.168.1.1'):
        """Add interfaces
        
        @param interfaces list of interfaces
        """

        #Set up interfaces
        self.loif = self.add_loif("local")
        self.add_interfaces(interfaces)

        #Get IP addresses on the interfaces
        self.ifmgr.set_ipv4_addr(self.loif.client_intf, inner_addr)
        for i in range(0, len(interfaces)):
            self.ifmgr.up(interfaces[i])
        
    def add_interfaces(self, interfaces):
        """Add interfaces (plus mirror port)
        
        @param interfaces list of interfaces
        """
        for i in interfaces:
            self.switch.add_if(i)
            self.ifmgr.set_ipv4_addr(i, '0.0.0.0')
            #Add mirror interface
            self.mirror[i] = self.add_loif(i)
            self.ifmgr.set_eth_addr(self.mirror[i].client_intf,
                                    self.ifmgr.ethernet_addr(i))
            np = self.switch.get_ports()
            port1 = np[i]
            port2 = np[self.mirror[i].switch_intf]

            #Set perm ARP rules for mirror
            ae1 = flows.arp_entry(priority=ofutil.PRIORITY['LOW'])
            ae1.set_in_port(port1)
            ae1.add_output(port2, 65535)
            self.default.add_perm(ae1)
            ae2 = flows.arp_entry(priority=ofutil.PRIORITY['LOW'])
            ae2.set_in_port(port2)
            ae2.add_output(port1, 65535)
            self.default.add_perm(ae2)
            #Set perm DHCP rules for mirror
            dreq = flows.udp_entry(portno=68,
                                   priority=ofutil.PRIORITY['LOW'])
            dreq.set_in_port(port1)
            dreq.add_output(port2, 65535)
            self.default.add_perm(dreq)
            drep = flows.udp_entry(portno=67,
                                   priority=ofutil.PRIORITY['LOW'])
            drep.set_in_port(port2)
            drep.add_output(port1, 65535)
            self.default.add_perm(drep)           
            
            output.dbg("Set "+self.mirror[i].client_intf+" to "+self.ifmgr.ethernet_addr(i),
                       self.__class__.__name__)
            

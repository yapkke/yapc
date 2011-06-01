##COIN NAT
#
# Client-side OpenFlow Interface for Networking (NAT Mode)
#
# @author ykk
# @date May 2011
#
import yapc.interface as yapc
import yapc.coin.core as core
import yapc.forwarding.flows as flows
import yapc.util.openflow as ofutil
import yapc.log.output as output
import yapc.events.openflow as ofevents
import yapc.comm.json as jsoncomm
import yapc.util.memcacheutil as mc

LOCAL_IP = "192.168.4.1"
LOCAL_GW = "192.168.4.254"
MAX_RETRY = 7

class nat(core.coin_server):
    """Class to handle connections and configuration for COIN in NAT mode

    Mirror interfaces for DHCP and ARP.

    @author ykk
    @date May 2011
    """
    ##Prefix for gateway for interface
    GW_KEY_PREFIX="COIN_GW_"
    ##Prefix for mac for gateway
    GW_MAC_KEY_PREFIX="COIN_GW_MAC_"
    def __init__(self, server, ofconn, jsonconn):
        """Initialize

        @param server yapc core server/scheduler
        @param ofconn OpenFlow connections
        @param jsonconn JSON connections
        """
        core.coin_server.__init__(self, server, ofconn, jsonconn, False)
        ##Mode
        self.config["mode"] = "Multi-Homed (NATed)"
        ##Reference to local interface
        self.loif = None
        ##Mirror interfaces (indexed by primary interface)
        self.mirror = {}
        
        mc.get_client()
        server.register_event_handler(ofevents.error.name,
                                      self)
        server.register_event_handler(jsoncomm.message.name,
                                      self)

    def get_gw_key(intf):
        """Get memcache key for gw address for interface

        @param intf interface name
        """
        return nat.GW_KEY_PREFIX+str(intf).replace(" ","_")
    get_gw_key = yapc.static_callable(get_gw_key)

    def get_gw_mac_key(ip):
        """Get memcache key for mac address for gateway
        
        @param ip ip address of gateway
        """
        return nat.GW_MAC_KEY_PREFIX+str(ip).replace(" ","_").replace(".","-")
    get_gw_mac_key = yapc.static_callable(get_gw_mac_key)        

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

    def setup(self, interfaces, inner_addr=LOCAL_IP, gw=LOCAL_GW,
              gw_mac=None):
        """Add interfaces
        
        @param interfaces list of interfaces
        @param inner_addr IP to give COIN's client side interface
        @param gw gateway to use for COIN's interface
        @param gw_mac gateway mac address
        """
        #Set up interfaces
        self.loif = self.add_loif("local")
        self.add_interfaces(interfaces)

        #Get IP addresses on the interfaces
        self.ifmgr.set_ipv4_addr(self.loif.client_intf, inner_addr)
        for i in range(0, len(interfaces)):
            self.ifmgr.up(interfaces[i])

        #Setup route
        self.ifmgr.add_route("default", gw=gw, 
                             iface=self.loif.client_intf)
        if (gw_mac == None):
            gw_mac = self.ifmgr.ethernet_addr(self.loif.switch_intf)
        self.ifmgr.set_ip_mac(gw, gw_mac)
 
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
        elif (event.message["command"] == "dhclient"):
            reply["dhclient result"] = self.dhclient_mirror(event.message["name"])
        else:
            output.dbg("Receive message "+str(event.message),
                       self.__class__.__name__)
            return None

        return reply
            
    def __arp_check(self, o):
        """Check ARP
        
        @param o arp check object (dictionary)
        """
        mac = self.get_ip_mac(o["ip"], o["if"])
        if (mac == None):
            o["tried"] += 1
            if (o["tried"] < MAX_RETRY):
                rc = yapc.priv_callback(self, o)
                self.server.post_event(rc, 1)
        else:
            mc.set(nat.get_gw_mac_key(o["ip"]), mac.mac)
            output.info("ARP of "+o["ip"]+" is "+str(mac.mac),
                        self.__class__.__name__)
            self.check_default_route()

    def check_default_route(self):
        """Check default route and set it right
        """
        addlo = True
        self.ifmgr.query_route()
        routes = self.ifmgr.get_route()
        intfs = []
        for p,m in self.mirror.items():
            intfs.append(p)
            intfs.append(m.client_intf)

        for r in routes:
            if (r.destination == "0.0.0.0"):
                if (r.iface == self.loif.client_intf):
                    addlo = False
                else:
                    self.ifmgr.del_route("default", iface=r.iface)
                    output.dbg("Deleting route:\n\t"+str(r),
                               self.__class__.__name__)
            elif (r.iface in intfs):
                self.ifmgr.del_route("-net "+r.destination,
                                     netmask=r.mask, iface=r.iface)

        if (addlo):
            self.ifmgr.add_route("default", iface=self.loif.client_intf)
            output.dbg("Add default route for COIN",
                       self.__class__.__name__)
        

    def __route_check(self, o):
        """Check route
        
        @param o route check object (dictionary)
        """
        gw = self.get_if_route(mif=o["mif"])
        if (gw == None):
            o["tried"] += 1
            if (o["tried"] < MAX_RETRY):
                rc = yapc.priv_callback(self, o)
                self.server.post_event(rc, 1)
        else:
            mc.set(nat.get_gw_key(o["if"]), gw)
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

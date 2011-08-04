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
import yapc.util.parse as pu
import yapc.log.output as output
import yapc.events.openflow as ofevents
import yapc.comm.json as jsoncomm
import yapc.util.memcacheutil as mc
import yapc.pyopenflow as pyof
import yapc.packet.ofaction as ofpkt
import dpkt
import simplejson
import random

LOCAL_IP = "192.168.4.1"
LOCAL_GW = "192.168.4.254"
MAX_RETRY = 10

class nat(core.coin_server):
    """Class to handle connections and configuration for COIN in NAT mode

    Mirror interfaces for DHCP and ARP.

    @author ykk
    @date May 2011
    """
    ##Key for inner port
    SW_INNER_PORT = "COIN_SW_INNER_PORT"
    ##Key for inner ip and mac
    SW_INNER_PORT_ADDR = "COIN_SW_INNER_PORT_ADDR"
    ##Key for switch feature
    SW_FEATURE = "COIN_SW_FEATURE"
    ##Prefix for gateway for interface   
    IP_RANGE_KEY_PREFIX = "COIN_IP_RANGE_"
    ##Prefix for gateway for interface
    GW_KEY_PREFIX = "COIN_GW_"
    ##Prefix for mac for gateway
    GW_MAC_KEY_PREFIX = "COIN_GW_MAC_"
    def __init__(self, server, ofconn, jsonconn):
        """Initialize

        @param server yapc core server/scheduler
        @param ofconn OpenFlow connections
        @param jsonconn JSON connections
        """
        core.coin_server.__init__(self, server, ofconn, jsonconn, False)
        ##Mode
        self.config["mode"] = "Multi-Homed (NATed)"
        self.config["select_interface"] = 1
        ##Reference to local interface
        self.loif = None
        ##Mirror interfaces (indexed by primary interface)
        self.mirror = {}
        
        mc.get_client()
        server.register_event_handler(ofevents.error.name,
                                      self)
        server.register_event_handler(ofevents.features_reply.name,
                                      self)
        server.register_event_handler(ofevents.port_status.name,
                                      self)
        server.register_event_handler(jsoncomm.message.name,
                                      self)

    def get_gw_key(portno):
        """Get memcache key for gw address for interface

        @param portno port no of the interface
        """
        return nat.GW_KEY_PREFIX+str(portno).strip()
    get_gw_key = yapc.static_callable(get_gw_key)

    def get_gw_mac_key(ip):
        """Get memcache key for mac address for gateway
        
        @param ip ip address of gateway
        """
        return nat.GW_MAC_KEY_PREFIX+str(ip).replace(" ","_").replace(".","-")
    get_gw_mac_key = yapc.static_callable(get_gw_mac_key)        

    def get_ip_range_key(portno):
        """Get memcache key for IP address range for a particular interface
        
        @param portno port no of the interface
        """
        return nat.IP_RANGE_KEY_PREFIX+str(portno).strip()
    get_ip_range_key = yapc.static_callable(get_ip_range_key)

    def processevent(self, event):
        """Process OpenFlow and JSON messages

        @param event event to handle
        @return True
        """
        if (isinstance(event, ofevents.features_reply) or
            isinstance(event, ofevents.port_status)):
            self.update_sw_feature()
        elif isinstance(event, ofevents.error):
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
        mc.set(nat.SW_INNER_PORT_ADDR, 
               (pu.ip_string2val(inner_addr), 
                pu.hex_str2array(self.ifmgr.ethernet_addr(self.loif.client_intf))))
        for i in range(0, len(interfaces)):
            self.ifmgr.up(interfaces[i])

        #Setup route
        self.ifmgr.add_route("default", gw=gw, 
                             iface=self.loif.client_intf)
        if (gw_mac == None):
            gw_mac = self.ifmgr.ethernet_addr(self.loif.switch_intf)
        self.ifmgr.set_ip_mac(gw, gw_mac)

        self.check_default_route()

    def update_sw_feature(self):
        """Update switch feature in memcache
        """
        sf = self.switch.get_sw_feature()
        if (sf == None):
            output.warn("No switch features!!!",
                        self.__class__.__name__)
        else:
            output.dbg("Set switch feature as "+sf.show(),
                       self.__class__.__name__)
            mc.set(nat.SW_FEATURE, sf)
        
        iport = self.switch.if_name2dpid_port_mac(self.loif.switch_intf)[1]
        if (iport == None):
            output.warn("No inner port!!!",
                        self.__class__.__name__)
        else:
            output.dbg("Set inner port as "+str(iport),
                       self.__class__.__name__)
            mc.set(nat.SW_INNER_PORT, iport)
 
    def add_interfaces(self, interfaces):
        """Add interfaces (plus mirror port)
        
        @param interfaces list of interfaces
        """
        for i in interfaces:
            self.switch.add_if(i)
            self.ifmgr.set_ipv4_addr(i, '0.0.0.0')
            #Add mirror interface
            self.mirror[i] = self.add_loif(i)
            ieth = self.ifmgr.ethernet_addr(i)
            self.ifmgr.set_eth_addr(self.mirror[i].client_intf, ieth)
            np = self.switch.get_ports()
            port1 = np[i]
            port2 = np[self.mirror[i].switch_intf]
            
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
        mac = self.get_ip_mac(o["ip"], self.loif.client_intf)
        if (mac == None):
            o["tried"] += 1
            if (o["tried"] < MAX_RETRY):
                rc = yapc.priv_callback(self, o)
                self.server.post_event(rc, 1)
        else:
            mc.set(nat.get_gw_mac_key(o["ip"]), mac.mac)
            output.info("ARP of "+o["ip"]+" is "+str(mac.mac),
                        self.__class__.__name__)

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
            elif (r.iface in intfs):
                self.ifmgr.del_route("-net "+r.destination,
                                     netmask=r.mask, iface=r.iface)
                self.ifmgr.add_route("-net "+r.destination,
                                     netmask=r.mask, iface=self.loif.client_intf)

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
            no = self.switch.if_name2dpid_port_mac(o["if"])[1]
            mc.set(nat.get_gw_key(no), gw)
            output.info("Gateway of "+o["if"]+" is "+gw,
                        self.__class__.__name__)
            #Check for route
            self.check_default_route()
             #Register ip range
            ipv4addr = self.ifmgr.ipv4_addr_n_mask(o["mif"])
            ipr = (pu.ip_string2val(ipv4addr["addr"]),
                   pu.ip_string2val(ipv4addr["netmask"]),
                   pu.hex_str2array(self.ifmgr.ethernet_addr(o["mif"])))
            mc.set(nat.get_ip_range_key(no), ipr)
            output.info(o["if"]+"("+str(no)+") has IP address %x and netmask %x" % (ipr[0], ipr[1]),
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

class arp_handler(core.component):
    """Class to handle arp in COIN

    @author ykk
    @date Jun 2011
    """
    def __init__(self, server, ofconn):
        """Initialize

        @param server yapc core
        @param conn reference to connections
        @param sfr send flow removed or not
        """
        core.component.__init__(self, ofconn)

        mc.get_client()
        server.register_event_handler(ofevents.pktin.name, self)
        
    def processevent(self, event):
        """Event handler (for ARP only)

        @param event event to handle
        @return false if processed else true
        """
        if (isinstance(event, ofevents.pktin) and
            event.match.dl_type == dpkt.ethernet.ETH_TYPE_ARP):
            iport = mc.get(nat.SW_INNER_PORT)
            intfs = self.get_intf_n_range()
            lointf = mc.get(nat.SW_INNER_PORT_ADDR)
            if (iport == None):
                output.err("No inner port recorded!  Are we connected?",
                           self.__class__.__name__)
                return True

            if (event.match.in_port == iport):
                return self._process_self_initiated(event, intfs, iport, lointf)
            else:
                return self._process_peer_initiated(event, intfs, iport, lointf)

        return True     

    def get_intf_n_range(self):
        """Retrieve dictionary of interface and their ip range
        """
        r = {}
        sf = mc.get(nat.SW_FEATURE)
        for p in sf.ports:
            ipr = mc.get(nat.get_ip_range_key(p.port_no))
            if (ipr != None):
                r[p.port_no] = ipr
        return r

    def _process_self_initiated(self, pktin, intfs, iport, lointf):
        """Event handler for self_initiated packet

        @param pktin packet in event to handle
        @param intfs dictionary of interfaces (with ip range)
        @param iport port no of local interface
        @param lointf local interface address (ip, mac)
        @return false
        """
        for portno,ipr in intfs.items():
            if ((ipr[0] & ipr[1]) == (pktin.match.nw_dst & ipr[1])):
                #Local address                
                flow = flows.exact_entry(pktin.match)
                flow.set_buffer(pktin.pktin.buffer_id)
                flow.add_dl_rewrite(True, ipr[2])
                flow.add_output(portno)               
                ofpkt.dl_rewrite(pktin.dpkt, True, ipr[2])
                ofpkt.nw_rewrite(pktin.dpkt, True, ipr[0])
                self.get_conn().send(flow.get_packet_out().pack()+\
                                         pktin.dpkt.pack())
        return False

    def _process_peer_initiated(self, pktin, intfs, iport, lointf):
        """Event handler for peer_initiated packet

        @param pktin packet in event to handle
        @param intfs dictionary of interfaces (with ip range)
        @param iport port no of local interface
        @param lointf local interface address (ip, mac)
        @return false
        """
        bcast = (pu.array2val(pktin.match.dl_dst)== 0xffffffffffff)
        for portno,ipr in intfs.items():
            if ((ipr[2] == pktin.match.dl_dst) or bcast):
                flow = flows.exact_entry(pktin.match)
                flow.set_buffer(pktin.pktin.buffer_id)
                if (not bcast):
                    flow.add_dl_rewrite(False, lointf[1])
                flow.add_output(iport)

                if (pktin.match.nw_proto == dpkt.arp.ARP_OP_REPLY):
                    ofpkt.dl_rewrite(pktin.dpkt, False, lointf[1])
                ofpkt.nw_rewrite(pktin.dpkt, False, lointf[0])
                self.get_conn().send(flow.get_packet_out().pack()+\
                                         pktin.dpkt.pack())
        return False

class ip_handler(core.component):
    """Class to handle local IP traffic

    @author ykk
    @date Jun 2011
    """
    def __init__(self, server, ofconn, coin=None):
        """Initialize

        @param server yapc core
        @param conn reference to connections
        @param sfr send flow removed or not
        """
        core.component.__init__(self, ofconn, coin)

        mc.get_client()
        server.register_event_handler(ofevents.pktin.name, self)
        
        ##Reference to last interface chosen
        self.__last_intf_choosen = 0

    def processevent(self, event):
        """Event handler

        @param event event to handle
        @return false if processed else true
        """
        if isinstance(event, ofevents.pktin):
            iport = mc.get(nat.SW_INNER_PORT)
            intfs = self.get_intf_n_range()
            lointf = mc.get(nat.SW_INNER_PORT_ADDR)
            if (iport == None):
                output.err("No inner port recorded!  Are we connected?",
                           self.__class__.__name__)
                return True

            if (event.match.in_port == iport):
                return self._process_self_initiated(event, intfs, iport, lointf)
            else:
                return self._process_peer_initiated(event, intfs, iport, lointf)

        return True     

    def select_intf(self, intfs):
        """Get which interface to send

        @return port no to send flow on and None if nothing to choose from
        """
        if (len(intfs) == 0):
            return None

        if (self.coin == None):
            output.warn("No COIN server reference provided.  Default to random choice of interface",
                        self.__class__.__name__)
            return self.select_nth_intf(intfs, 1)

        if (self.coin.config["select_interface"] == "random"):
            return self.random_select_intf(intfs)
        elif (self.coin.config["select_interface"] == "round_robin"):
            return self.round_robin_select_intf(intfs)
        elif (isinstance(self.coin.config["select_interface"], int)):
            return self.select_nth_intf(intfs, self.coin.config["select_interface"])
        else:
            value = 1
            try:
                value = int(self.coin.config["select_interface"])
                self.coin.set_config("select_interface", value)
            except ValueError:
                output.warn("Unknown selection configuration!",
                            self.__class__.__name__)
            return self.select_nth_intf(intfs, value)

    def select_nth_intf(self, intfs, index=1):
        """Get which interface to send (always return nth interface else last)

        @return port no to send flow on and None if nothing to choose from
        """
        c = intfs.keys()[0]
        i = index-1
        if ((i > 0) and (i < len(intfs))):
            c = intfs.keys()[i]
        output.dbg("Port "+str(c)+" "+str(intfs[c])+" selected 'cos it is "+\
                       str(index)+"st/nd/rd/th interface",
                   self.__class__.__name__)
        return c

    def random_select_intf(self, intfs):
        """Get which interface to send (random choice)

        @return port no to send flow on and None if nothing to choose from
        """
        c = random.choice(intfs.keys())
        output.dbg("Port "+str(c)+" "+str(intfs[c])+" randomly selected",
                   self.__class__.__name__)
        return c

    def round_robin_select_intf(self, intfs):
        """Get which interface to send (round robin)

        @return port no to send flow on and None if nothing to choose from
        """
        choices = intfs.keys()

        self.__last_intf_choosen += 1
        if (self.__last_intf_choosen >= len(choices)):
            self.__last_intf_choosen = 0
        c = choices[self.__last_intf_choosen]
        output.dbg("Port "+str(c)+" "+str(intfs[c])+" selected via round robin",
                   self.__class__.__name__)
        return c

    def get_intf_n_range(self):
        """Retrieve dictionary of interface and their ip range
        """
        r = {}
        sf = mc.get(nat.SW_FEATURE)
        for p in sf.ports:
            ipr = mc.get(nat.get_ip_range_key(p.port_no))
            if (ipr != None):
                r[p.port_no] = ipr
        return r

    def _process_self_initiated(self, pktin, intfs, iport, lointf):
        """Event handler for self_initiated packet

        @param pktin packet in event to handle
        @param intfs dictionary of interfaces (with ip range)
        @param iport port no of local interface
        @param lointf local interface address (ip, mac)
        @return false if processed else true
        """
        for portno,ipr in intfs.items():
            if ((ipr[0] & ipr[1]) == (pktin.match.nw_dst & ipr[1])):
                #Local address                
                flow = flows.exact_entry(pktin.match)
                flow.set_buffer(pktin.pktin.buffer_id)
                flow.add_nw_rewrite(True, ipr[0])
                flow.add_dl_rewrite(True, ipr[2])
                flow.add_output(portno)
                self.get_conn().send(flow.get_flow_mod(pyof.OFPFC_ADD).pack())
                return False

        if (pu.array2val(pktin.match.dl_dst)== 0xffffffffffff):
            return True

        #Global address
        cport = self.select_intf(intfs)
        if (cport != None):
            gw = mc.get(nat.get_gw_key(cport))
            gwmac = mc.get(nat.get_gw_mac_key(gw))
            ipr = intfs[cport]
            if ((gw == None) or (gwmac == None)):
                output.warn("Packet ignored since gateway for interface not found!",
                            self.__class__.__name__)
                return False

            flow = flows.exact_entry(pktin.match)
            flow.add_nw_rewrite(True, ipr[0])
            flow.add_dl_rewrite(True, ipr[2])
            flow.add_dl_rewrite(False, pu.hex_str2array(gwmac))
            flow.add_output(cport)
            if (pktin.pktin.buffer_id == flow.buffer_id):
                ofpkt.nw_rewrite(pktin.dpkt, True, ipr[0])
                ofpkt.dl_rewrite(pktin.dpkt, True, ipr[2])
                ofpkt.dl_rewrite(pktin.dpkt, False, pu.hex_str2array(gwmac))
                self.get_conn().send(flow.get_flow_mod(pyof.OFPFC_ADD).pack())
                self.get_conn().send(flow.get_packet_out(pyof.OFPFC_ADD).pack()+\
                                         pktin.dpkt.pack())
            else:
                flow.set_buffer(pktin.pktin.buffer_id)
                self.get_conn().send(flow.get_flow_mod(pyof.OFPFC_ADD).pack())
            return False

        return True

    def _process_peer_initiated(self, pktin, intfs, iport, lointf):
        """Event handler for peer_initiated packet

        @param pktin packet in event to handle
        @param intfs dictionary of interfaces (with ip range)
        @param iport port no of local interface
        @param lointf local interface address (ip, mac)
        @return false
        """
        flow = flows.exact_entry(pktin.match)
        for portno,ipr in intfs.items():
            if ((ipr[0] & ipr[1]) == (pktin.match.nw_src & ipr[1])):
                if ((ipr[2] == pktin.match.dl_dst)):
                    flow.add_nw_rewrite(False, lointf[0])
                    flow.add_dl_rewrite(False, lointf[1])
                    flow.add_output(iport)
                    if (pktin.pktin.buffer_id == flow.buffer_id):
                        ofpkt.nw_rewrite(pktin.dpkt, False, lointf[0])
                        ofpkt.dl_rewrite(pktin.dpkt, False, lointf[1])
                        self.get_conn().send(flow.get_flow_mod(pyof.OFPFC_ADD).pack())
                        self.get_conn().send(flow.get_packet_out(pyof.OFPFC_ADD).pack()+\
                                                 pktin.dpkt.pack())
                    else:
                        flow.set_buffer(pktin.pktin.buffer_id)
                        self.get_conn().send(flow.get_flow_mod(pyof.OFPFC_ADD).pack())
                return False

        if (pu.array2val(pktin.match.dl_dst)== 0xffffffffffff):
            return True

        #Global address
        flow.set_buffer(pktin.pktin.buffer_id)
        flow.add_nw_rewrite(False, lointf[0])
        flow.add_dl_rewrite(False, lointf[1])
        flow.add_output(iport)
        if (pktin.pktin.buffer_id == flow.buffer_id):
            ofpkt.nw_rewrite(pktin.dpkt, False, lointf[0])
            ofpkt.dl_rewrite(pktin.dpkt, False, lointf[1])
            self.get_conn().send(flow.get_flow_mod(pyof.OFPFC_ADD).pack())
            self.get_conn().send(flow.get_packet_out(pyof.OFPFC_ADD).pack()+\
                                     pktin.dpkt.pack())
        else:
            flow.set_buffer(pktin.pktin.buffer_id)
            self.get_conn().send(flow.get_flow_mod(pyof.OFPFC_ADD).pack())
        
        gw = mc.get(nat.get_gw_key(flow.match.in_port))
        gwmac = mc.get(nat.get_gw_mac_key(gw))
        if (gwmac == None):
            return False
        try:
            ipr = intfs[flow.match.in_port]
        except KeyError:
            return False

        rflow = flow.reverse(iport)
        rflow.match.nw_src = lointf[0]
        rflow.match.dl_src = lointf[1]
        rflow.match.wildcards -= pyof.OFPFW_DL_DST
        rflow.add_nw_rewrite(True, ipr[0])
        rflow.add_dl_rewrite(True, ipr[2])
        rflow.add_dl_rewrite(False, pu.hex_str2array(gwmac))
        rflow.add_output(flow.match.in_port)
        self.get_conn().send(rflow.get_flow_mod(pyof.OFPFC_ADD).pack())
        
        return False


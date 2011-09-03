##COIN NAT
#
# Client-side OpenFlow Interface for Networking (Bridge Mode)
#
# @author ykk
# @date Sept 2011
#
import yapc.coin.core as core
import yapc.log.output as output
import yapc.util.memcacheutil as mc
import yapc.events.openflow as ofevents
import yapc.comm.json as jsoncomm
import yapc.comm.udpjson as udpjson
import yapc.forwarding.flows as flows
import yapc.pyopenflow as pyof
import yapc.util.parse as pu
import simplejson
import dpkt

class bridge(core.coin_server):
    """Class to handle connections and configuration for COIN in Bridge mode

    @author ykk
    @date Sept 2011
    """
    ##Key for inner port
    SW_INNER_PORT = "COIN_SW_INNER_PORT"
    ##Key for switch feature
    SW_FEATURE = "COIN_SW_FEATURE"
    def __init__(self, server, ofconn, jsonconn):
        """Initialize

        @param server yapc core server/scheduler
        @param ofconn OpenFlow connections
        @param jsonconn JSON connections
        """
        core.coin_server.__init__(self, server, ofconn, jsonconn, False)
        ##Mode
        self.config["mode"] = "Multi-Homed (Bridged)"
        self.config["select_interface"] = 1
        ##Reference to local interface
        self.loif = None
        
        mc.get_client()

        server.register_event_handler(ofevents.error.name,
                                      self)
        server.register_event_handler(ofevents.features_reply.name,
                                      self)
        server.register_event_handler(ofevents.port_status.name,
                                      self)
        server.register_event_handler(jsoncomm.message.name,
                                      self)

    def setup(self, interfaces, inner_mac=None):
        """Add interfaces
        
        @param interfaces list of interfaces
        """
        #Set up interfaces
        self.loif = self.add_loif("local")
        self.add_interfaces(interfaces)

        #Clean up device setting
        for i in range(0, len(interfaces)):
            self.ifmgr.up(interfaces[i])
            self.ifmgr.set_ipv4_addr(interfaces[i], "0.0.0.0")
        self.ifmgr.del_default_routes()

        if (inner_mac == None) and (len(interfaces) > 0):
            inner_mac = self.ifmgr.ethernet_addr(interfaces[0])

        if (inner_mac != None):
            self.ifmgr.set_eth_addr(self.loif.client_intf, inner_mac)

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
            mc.set(bridge.SW_FEATURE, sf)
        
        iport = self.switch.if_name2dpid_port_mac(self.loif.switch_intf)[1]
        if (iport == None):
            output.warn("No inner port!!!",
                        self.__class__.__name__)
        else:
            output.dbg("Set inner port as "+str(iport),
                       self.__class__.__name__)
            mc.set(bridge.SW_INNER_PORT, iport)

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

class traffic_handler(core.component):
    """Class to handle traffic

    @author ykk
    @date Sept 2011
    """
    def __init__(self, server, ofconn, coin=None):
        """Initialize

        @param server yapc core
        @param conn reference to connections
        @param sfr send flow removed or not
        @param coin reference to COIN
        @oaram bwinterval interval to query for bandwidth
        """
        core.component.__init__(self, ofconn, coin)
        
        mc.get_client()
        server.register_event_handler(ofevents.pktin.name, self)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        @return false if processed else true
        """
        if isinstance(event, ofevents.pktin):
            iport = mc.get(bridge.SW_INNER_PORT)
            intfs = self.get_ext_intf()
            if (iport == None):
                output.err("No inner port recorded!  Are we connected?",
                           self.__class__.__name__)
                return True

            flow = flows.exact_entry(event.match)
            if (event.match.in_port == iport):
                flow.add_output(self.get_out_port(intfs))
            else:
                flow.add_output(iport)

            if (flow.buffer_id != event.pktin.buffer_id):
                flow.set_buffer(event.pktin.buffer_id)
                self.get_conn().send(flow.get_flow_mod(pyof.OFPFC_ADD).pack())
            else:
                self.get_conn().send(flow.get_flow_mod(pyof.OFPFC_ADD).pack())
                self.get_conn().send(flow.get_packet_out(pyof.OFPFC_ADD).pack()+\
                                         event.dpkt.pack())
                return False

        return True     

    def get_ext_intf(self):
        """Retrieve dictionary of external ports
        """
        r = {}
        sf = mc.get(bridge.SW_FEATURE)
        iport = mc.get(bridge.SW_INNER_PORT)
        for p in sf.ports:
            if (p.port_no != iport) and (p.port_no <= pyof.OFPP_MAX):
                r[p.port_no] = p.name
            
        return r

    def get_out_port(self, intfs):
        """Get output port for outbound traffic

        @param intfs interfaces to choose from
        """
        if (len(intfs) == 0):
            return None

        if (self.coin == None):
            output.warn("No COIN server reference provided.  Default to random choice of interface",
                        self.__class__.__name__)
            return self.select_nth_intf(intfs, 1)

        if (isinstance(self.coin.config["select_interface"], int)):
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

class host_move(core.component):
    """Class to handle address change
    
    Code does not handle IP changes to local IP (since we need to arp in that case)

    @author ykk
    @date Sept 2011
    """
    def __init__(self, server, ofconn, coin=None):
        """Initialize

        @param server yapc core
        @param conn reference to connections
        @param sfr send flow removed or not
        @param coin reference to COIN
        @oaram bwinterval interval to query for bandwidth
        """
        core.component.__init__(self, ofconn, coin)
        ##Keep state of new ip indexed by old ip
        self.ip_change = {}

        server.register_event_handler(udpjson.message.name, self)
        server.register_event_handler(ofevents.flow_stats.name, self)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        @return True
        """
        if isinstance(event, udpjson.message):
            self._handle_json(event)
        elif isinstance(event, ofevents.flow_stats):
            self._handle_change(event)

        return True

    def _handle_change(self, flow_stats):
        """Handle flows to be changed based on flow stats reply
        
        @param flow_stats flow_stats event
        """
        for f in flow_stats.flows:
            for (old, new) in self.ip_change.items():
                if (f.match.nw_src == old):
                    flow = flows.exact_entry(f.match,
                                             priority=f.priority,
                                             idle_timeout=f.idle_timeout,
                                             hard_timeout=f.hard_timeout)
                    flow.set_nw_src(new)
                    flow.add_nw_rewrite(True, old)
                    flow.actions.extend(f.actions)
                    self.get_conn().send(flow.get_flow_mod(pyof.OFPFC_ADD, f.cookie).pack())
                    output.dbg(str(f)+" has old source IP", 
                               self.__class__.__name__)
                elif (f.match.nw_dst == old):
                    flow = flows.exact_entry(f.match,
                                             priority=f.priority,
                                             idle_timeout=f.idle_timeout,
                                             hard_timeout=f.hard_timeout)
                    flow.add_nw_rewrite(False, new)
                    flow.actions.extend(f.actions)
                    self.get_conn().send(flow.get_flow_mod(pyof.OFPFC_MODIFY, f.cookie).pack())
                    output.dbg(str(f)+" has old destination IP", 
                               self.__class__.__name__)

    def _handle_json(self, jsonmsg):
        """Handle JSON message
        """
        ##Add change to list
        old_ip = pu.ip_string2val(jsonmsg.json_msg["ip_prev"][0])
        self.ip_change[old_ip] = pu.ip_string2val(jsonmsg.json_msg["ip_new"][0])

        ##Send for flow stats
        flow = flows.ethertype_entry(dpkt.ethernet.ETH_TYPE_IP)
        flow.set_nw_src(old_ip)
        (sr, fsr) = flow.get_flow_stats_request()
        self.get_conn().send(sr.pack()+fsr.pack())

        flow = flows.ethertype_entry(dpkt.ethernet.ETH_TYPE_IP)
        flow.set_nw_dst(old_ip)
        (sr, fsr) = flow.get_flow_stats_request()
        self.get_conn().send(sr.pack()+fsr.pack())
        
        output.dbg(str(self.ip_change),
                   self.__class__.__name__)
        

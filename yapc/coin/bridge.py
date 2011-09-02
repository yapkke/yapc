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
import yapc.forwarding.flows as flows
import yapc.pyopenflow as pyof
import simplejson

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
        
        self.server = server

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

        

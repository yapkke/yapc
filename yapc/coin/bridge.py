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

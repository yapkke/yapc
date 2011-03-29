##State of switches
#
# Status of switches maintained
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.events.openflow as ofevents
import yapc.comm as comm
import yapc.output as output
import yapc.pyopenflow as pyof
import yapc.util.memcacheutil as mc

class dp_config(yapc.component):
    """Class to configure switches and maintain their config state

    Note that default_off_config_flags takes precedence over defailt_on_config_flags.

    Maintain 
    * set of datapath config keyed by (keys from get_key/socket name)

    @author ykk
    @date Mar 2011
    """
    ##Key prefix in memcache for config (with socket appended to the end)
    DP_CONFIG_KEY_PREFIX = "dp_config_"
    def __init__(self, server, ofconn):
        """Initialize

        @param server reference to yapc core
        @param ofconn connections to switches
        """
        #Start memcache
        output.dbg(mc.get_client(),
                   self.__class__.__name__)

        ##Reference to connections
        self.conn = ofconn

        ##Default config flags to be on (OR with config received)
        self.default_on_config_flags = 0
        ##Default config flags to be off (NOT and AND with config received)
        self.default_off_config_flags = 0
        ##Default config miss send len
        self.default_miss_send_len = None
        
        server.register_event_handler(ofevents.features_reply.name, self)
        server.register_event_handler(ofevents.config_reply.name, self)
        server.register_event_handler(comm.event.name, self)

    def get_key(sock):
        """Get key to retrieve key for datapath features

        @param sock socket
        """
        return dp_config.DP_CONFIG_KEY_PREFIX+mc.socket_str(sock)
    get_key = yapc.static_callable(get_key)

    def processevent(self, event):
        """Process OpenFlow message for config reply
        
        @param event OpenFlow message event to process
        @return True
        """
        if isinstance(event, ofevents.features_reply):
            #Get config
            getconfig = pyof.ofp_header()
            getconfig.type = pyof.OFPT_GET_CONFIG_REQUEST
            self.conn.db[event.sock].send(getconfig.pack())
        
        elif isinstance(event, ofevents.config_reply):
            #Check if I should set config
            desired_flags = ((event.config.flags | 
                              self.default_on_config_flags)
                             & ~self.default_off_config_flags)
            desired_miss_send_len = event.config.miss_send_len
            if (self.default_miss_send_len != None):
                desired_miss_send_len = self.default_miss_send_len
            if ((event.config.flags != desired_flags) or  
                (desired_miss_send_len != event.config.miss_send_len)):
                #Change config to desired
                output.dbg("Set config to desired with flag %x " % desired_flags +
                           "and miss_send_len "+str(desired_miss_send_len),
                           self.__class__.__name__)
                setconfig = pyof.ofp_switch_config()
                setconfig.header.type = pyof.OFPT_SET_CONFIG
                setconfig.flags = desired_flags
                setconfig.miss_send_len = desired_miss_send_len
                self.conn.db[event.sock].send(setconfig.pack())
            
                #Get config again after set
                getconfig = pyof.ofp_header()
                getconfig.type = pyof.OFPT_GET_CONFIG_REQUEST
                self.conn.db[event.sock].send(getconfig.pack())
            else:
                #Remember config
                key = self.get_key(event.sock)
                mc.set(key, event.config)
                output.dbg("Updated config with key "+key,
                           self.__class__.__name__)

        elif isinstance(event, comm.event):
            #Socket close, so remove config
            if (event.event == comm.event.SOCK_CLOSE):
                key = self.get_key(event.sock)
                c = mc.get(key)
                if (c != None):
                    mc.delete(key)

        return True

class dp_features(yapc.component):
    """Class to maintain datapath state passively

    Listen passively to FEATURES_REPLY and PORT_STATUS and
    comm.event for socket close

    Maintain two memcache items
    * list of keys from get_key/socket name
    * set of datapath features keyed by (keys from get_key/socket name)
    
    @author ykk
    @date Feb 2011
    """
    #Key for list of datapath ids
    DP_SOCK_LIST = "dp_features_sock_list"
    ##Key prefix in memcache for features (with socket appended to the end)
    DP_FEATURES_KEY_PREFIX = "dp_features_"
    def __init__(self, server):
        """Initialize

        @param server yapc core
        """
        #Start memcache
        mc.get_client()

        server.register_event_handler(ofevents.port_status.name, self)
        server.register_event_handler(ofevents.features_reply.name, self)
        server.register_event_handler(comm.event.name, self)

    def get_key(sock):
        """Get key to retrieve key for datapath features

        @param sock socket
        """
        return dp_features.DP_FEATURES_KEY_PREFIX+mc.socket_str(sock)
    get_key = yapc.static_callable(get_key)
            
    def processevent(self, event):
        """Process OpenFlow message for switch status
        
        @param event OpenFlow message event to process
        @return True
        """
        if isinstance(event, ofevents.features_reply):
            #Maintain list of datapath socket
            key = self.get_key(event.sock)
            dpidsl = mc.get(dp_features.DP_SOCK_LIST)
            if (dpidsl == None):
                dpidsl = []
            if (key not in dpidsl):
                dpidsl.append(key)
            mc.set(dp_features.DP_SOCK_LIST, dpidsl)

            #Maintain dp features in memcache
            mc.set(key, event.features)

        elif isinstance(event, ofevents.port_status):
            #Port status
            if (event.header.type == pyof.OFPT_PORT_STATUS):
                key = self.get_key(event.sock)
                sw = mc.get(key)
                if (sw == None):
                    output.warn("Port status from unknown datapath",
                                self.__class__.__name__)
                else:
                    output.dbg("Received port status:\n"+\
                                   event.port.show("\t"),
                               self.__class__.__name__)
                    if (event.port.reason == pyof.OFPPR_DELETE or 
                        event.port.reason == pyof.OFPPR_MODIFY):
                        for p in sw.ports:
                            if (p.port_no == event.port.desc.port_no):
                                sw.ports.remove(p)
                    if (event.port.reason == pyof.OFPPR_ADD or 
                        event.port.reason == pyof.OFPPR_MODIFY):
                        sw.ports.append(event.port.desc)
                    output.dbg("Updated switch features:\n"+\
                                   sw.show("\t"),
                               self.__class__.__name__)
                    mc.set(key, sw)

        elif isinstance(event, comm.event):
            #Socket close
            if (event.event == comm.event.SOCK_CLOSE):
                key = self.get_key(event.sock)
                sw = mc.get(key)
                if (sw != None):
                    output.info("Datapath %x leaves" % sw.datapath_id,
                                self.__class__.__name__)
                    #Maintain list of datapath socket
                    dpidsl = mc.get(dp_features.DP_SOCK_LIST)
                    if (dpidsl != None):
                        if (key in dpidsl):
                            dpidsl.remove(key)
                        mc.set(dp_features.DP_SOCK_LIST, dpidsl)

                    #Remove features
                    mc.delete(key)

        return True

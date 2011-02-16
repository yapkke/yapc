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
import yapc.memcacheutil as mc

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

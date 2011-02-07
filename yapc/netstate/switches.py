##State of switches
#
# Status of switches maintained
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.ofcomm as ofcomm
import yapc.output as output
import yapc.pyopenflow as pyof
import yapc.memcacheutil as mc

class dp_features(yapc.component):
    """Class to maintain datapath state passively

    Listen passively to FEATURES_REPLY and PORT_STATUS

    Maintain two memcache items
    * list of datapathid
    * set of datapath features keyed by keys from get_key
    
    @author ykk
    @date Feb 2011
    """
    #Key for list of datapath ids
    DP_LIST = "dp_features_list"
    ##Key prefix in memcache for features (with socket appended to the end)
    DP_FEATURES_KEY_PREFIX = "dp_features_"
    def __init__(self):
        """Initialize
        """
        #Start memcache
        mc.get_client()

    def get_key(sock):
        """Get key to retrieve key for datapath features

        @param sock socket
        """
        return dp_features.DP_FEATURES_KEY_PREFIX+str(`sock`).replace(" ","").strip()
    get_key = yapc.static_callable(get_key)

    def get_sock_key(socket):
        """Get key to retrieve key for datapath features

        @param datapathid datapathid
        """
        return dp_features.DP_FEATURES_KEY_PREFIX+("%x" % datapathid)
    get_sock_key = yapc.static_callable(get_sock_key)
            
    def processevent(self, event):
        """Process OpenFlow message for switch status
        
        @param event OpenFlow message event to process
        @return True
        """
        if isinstance(event, ofcomm.message):
            #Feature replies
            if (event.header.type == pyof.OFPT_FEATURES_REPLY):
                f = pyof.ofp_switch_features()
                r = f.unpack(event.message)
                while (len(r) >= pyof.OFP_PHY_PORT_BYTES):
                    p = pyof.ofp_phy_port()
                    r = p.unpack(r)
                    f.ports.append(p)
                if (len(r) > 0):
                    output.warn("Features reply is of irregular length with "+\
                                    str(len(r))+" bytes remaining.",
                                self.__class__.__name__)
                output.dbg("Received switch features:\n"+\
                               f.show("\t"),
                           self.__class__.__name__)

                #Maintain list of datapath ids
                dpidl = mc.get(dp_features.DP_LIST)
                if (dpidl == None):
                    dpidl = []
                if (f.datapath_id not in dpidl):
                    dpidl.append(f.datapath_id)
                mc.set(dp_features.DP_LIST, dpidl)

                #Maintain dp features in memcache
                mc.set(self.get_key(event.sock), f)

            #Port status
            elif (event.header.type == pyof.OFPT_PORT_STATUS):
                s = pyof.ofp_port_status()
                s.unpack(event.message)
                
                key = self.get_key(event.sock)
                sw = mc.get(key)
                if (sw == None):
                    output.err("Port status from unknown datapath",
                               self.__class__.__name__)
                else:
                    output.dbg("Received port status:\n"+\
                                   s.show("\t"),
                               self.__class__.__name__)
                    if (s.reason == pyof.OFPPR_DELETE or 
                        s.reason == pyof.OFPPR_MODIFY):
                        for p in self.switches[event.sock].ports:
                            if (p.port_no == s.desc.port_no):
                                sw.ports.remove(p)
                    if (s.reason == pyof.OFPPR_ADD or 
                        s.reason == pyof.OFPPR_MODIFY):
                        sw.ports.append(s.desc)
                    output.dbg("Updated switch features:\n"+\
                                   sw.show("\t"),
                               self.__class__.__name__)
                    mc.set(key, sw)

            #fixme (listen to datapath leave???)

        return True

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

class dp_features(yapc.component):
    """Class to maintain datapath state passively

    Listen passively to FEATURES_REPLY and PORT_STATUS
    
    @author ykk
    @date Feb 2011
    """
    def __init__(self):
        """Initialize
        """
        ##Dictionary of switches indexed by socket
        self.switches= {}
    
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
                self.switches[event.sock] = f

            #Port status
            elif (event.header.type == pyof.OFPT_PORT_STATUS):
                s = pyof.ofp_port_status()
                s.unpack(event.message)
                output.dbg("Received port status:\n"+\
                               s.show("\t"),
                           self.__class__.__name__)
                if (s.reason == pyof.OFPPR_DELETE or 
                    s.reason == pyof.OFPPR_MODIFY):
                    for p in self.switches[event.sock].ports:
                        if (p.port_no == s.desc.port_no):
                            self.switches[event.sock].ports.remove(p)
                if (s.reason == pyof.OFPPR_ADD or 
                    s.reason == pyof.OFPPR_MODIFY):
                    self.switches[event.sock].ports.append(s.desc)
                output.dbg("Updated switch features:\n"+\
                               self.switches[event.sock].show("\t"),
                           self.__class__.__name__)

        return True

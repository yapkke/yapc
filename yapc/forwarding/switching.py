##Switching mechanisms
#
# Forwarding that pertain to each individual switch
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.util.parse as pu
import yapc.events.openflow as ofevents
import yapc.netstate.swhost as swhost
import yapc.log.output as output
import yapc.pyopenflow as pyof
import yapc.util.memcacheutil as mc
import yapc.forwarding.flows as flows

class learningswitch(yapc.component):
    """Class to perform per flow learning switch

    Install flow rules with exact matches
    
    @author ykk
    @date Feb 2011
    """
    def __init__(self, server, ofconn, sfr=False):
        """Initialize

        @param server yapc core
        @param conn reference to connections
        @param sfr send flow removed or not
        """
        ##Reference to connections
        self.conn = ofconn
        ##Send flow removed of not
        self.send_flow_removed = sfr

        mc.get_client()
        server.register_event_handler(ofevents.pktin.name, self)
        server.register_event_handler(ofevents.flow_removed.name, self)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        @return false if flow can be installed, else true
        """
        if (isinstance(event, ofevents.pktin)):
            #Forward packet/flow
            if (pu.is_multicast_mac(event.match.dl_dst)):
                return True
            
            key = swhost.mac2sw_binding.get_key(event.sock,
                                                event.match.dl_dst)
            port = mc.get(key)
            if (port != None):
                self.installflow(event, port)
                return False
            else:
                output.dbg("No binding found for mac %x"  % pu.array2val(event.match.dl_dst),
                           self.__class__.__name__)
            
        return True     

    def installflow(self, event, port):
        """Install flow

        @param event packet-in event
        @param port port to send flow to
        """
        flow = flows.exact_entry(event.match)
        if (self.send_flow_removed):
            flow.set_flow_removed_flag()
        flow.set_buffer(event.pktin.buffer_id)
        flow.add_output(port)
        flow.install(self.conn, event.sock)
            

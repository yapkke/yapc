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
import yapc.output as output
import yapc.pyopenflow as pyof
import yapc.util.memcacheutil as mc
import yapc.forwarding.flows as flows

class learningswitch(yapc.component):
    """Class to perform per flow learning switch

    Install flow rules with exact matches
    
    @author ykk
    @date Feb 2011
    """
    def __init__(self, server, ofconn):
        """Initialize

        @param server yapc core
        @param conn reference to connections
        """
        ##Reference to connections
        self.conn = ofconn

        mc.get_client()
        server.register_event_handler(ofevents.pktin.name, self)

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
                output.dbg("No binding found for mac %x"  % pu.array2val(event.match.dl_dst))
            
            return True     

    def installflow(self, event, port):
        """Install flow

        @param event packet-in event
        @param port port to send flow to
        """
        flow = flows.exact_entry(event.match)
        flow.set_buffer(event.pktin.buffer_id)
        flow.add_output(port)
        
        #Install dropping flow
        self.conn.db[event.sock].send(flow.get_flow_mod(pyof.OFPFC_ADD).pack())
        output.vdbg("Install flow to port "+str(port)+\
                        " for packet with match "+\
                        event.match.show().replace('\n',';'))

        #Packet out if packet is not buffered
        if (event.pktin.buffer_id == flows.UNBUFFERED_ID):
            self.conn.db[event.sock].send(flow.get_packet_out().pack()+event.pkt)
            output.vdbg("Output unbuffered packet to port "+str(port)+\
                            " with match "+\
                            event.match.show().replace('\n',';'))
            

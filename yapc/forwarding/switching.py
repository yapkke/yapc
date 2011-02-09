##Switching mechanisms
#
# Forwarding that pertain to each individual switch
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.openflowutil as ofutil
import yapc.events.openflow as ofevents
import yapc.netstate.swhost as swhost
import yapc.memcacheutil as mc

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
        server.scheduler.registereventhandler(ofevents.pktin.name, self)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        @return false if flow can be installed, else true
        """
        if (isinstance(event, ofevents.pktin)):
            #Forward packet/flow
            key = swhost.mac2sw_binding.get_key(event.sock,
                                                event.match.dl_src)
            port = mc.get(key)
            if (port != None):
                installflow(event, port)
                return False
            
            return True     

    def installflow(self, event, port):
        """Install flow

        @param event packet-in event
        @param port port to send flow to
        """
        oao = pyof.ofp_action_output()
        oao.port = port
        
        #Install dropping flow
        fm = pyof.ofp_flow_mod()
        fm.header.xid = ofutil.get_xid()
        fm.match = event.match
        fm.command = pyof.OFPFC_ADD
        fm.idle_timeout = 5
        fm.buffer_id = event.pktin.buffer_id
        fm.actions.append(oao)
        self.conn.db[event.sock].send(fm.pack())

        output.vdbg("Install flow to port "+str(port)+\
                        " for packet with match "+\
                        event.match.show().replace('\n',';'))

        #Packet out if packet is not buffered
        po = pyof.ofp_packet_out()
        if (event.pktin.buffer_id == po.buffer_id):
            po.header.xid = fm.header.xid
            po.in_port = event.match.in_port
            po.actions_len = oao.len
            po.actions.append(oao)
            self.conn.db[event.sock].send(po.pack()+event.pkt)
            
            output.vdbg("Output unbuffered packet to port "+str(port)+\
                            " with match "+\
                            event.match.show().replace('\n',';'))
            

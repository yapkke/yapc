##Default forwarding actions
#
# Some forwarding ways of handling unhandled packets
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.output as output
import yapc.events.openflow as ofevents
import yapc.pyopenflow as pyof
import yapc.openflowutil as ofutil

class floodpkt(yapc.component):
    """Class that floods packet using packet out

    @author ykk
    @date Feb 2011
    """
    def __init__(self, server, ofconn):
        """Initialize

        @param server yapc core
        @param conn reference to connections
        """
        ##Reference to OpenFlow connections
        self.conn = ofconn

        server.register_event_handler(ofevents.pktin.name, self)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        """
        if (isinstance(event, ofevents.pktin)):
            oao = pyof.ofp_action_output()
            oao.port = pyof.OFPP_FLOOD

            po = pyof.ofp_packet_out()
            po.header.xid =  ofutil.get_xid()
            po.in_port = event.match.in_port
            po.actions_len = oao.len
            po.actions.append(oao)
            
            if (event.pktin.buffer_id == po.buffer_id):
                self.conn.db[event.sock].send(po.pack()+event.pkt)
                output.vdbg("Flood unbuffered packet with match "+\
                                event.match.show().replace('\n',';'))
          
            else:
                po.buffer_id = event.pktin.buffer_id
                self.conn.db[event.sock].send(po.pack())
                output.vdbg("Flood buffered packet with match "+\
                                event.match.show().replace('\n',';'))

        return True

class default_entries(yapc.component):
    """Class that install default entries during startup of switch

    @author ykk
    @date Feb 2011
    """
    def __init__(self, server, ofconn):
        """Initialize
        
        @param server yapc core
        @param ofconn refrence to connections
        """
        ##Reference to OpenFlow connections
        self.conn = ofconn
        ##List of entries to install
        self.entries = []

        server.register_event_handler(ofevents.features_reply.name, self)

    def add(self, flowentry):
        """Add flow entry to install
        """
        self.entries.append(flowentry)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        """
        if (isinstance(event, ofevents.features_reply)):
            for fm in self.entries:
                self.conn.db[event.sock].send(fm.get_flow_mod().pack())

        return True

class dropflow(yapc.component):
    """Class that drop flows

    @author ykk
    @date Feb 2011
    """
    def __init__(self, server, ofconn):
        """Initialize

        @param server yapc core
        @param conn reference to connections
        """
        ##Reference to OpenFlow connections
        self.conn = ofconn

        server.register_event_handler(ofevents.pktin.name, self)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        """
        if (isinstance(event, ofevents.pktin)):
            self.dropflow(event)

        return True

    def dropflow(self, event):
        """Drop flow

        @param event packet-in event
        """
        #Install dropping flow
        fm = pyof.ofp_flow_mod()
        fm.header.xid = ofutil.get_xid()
        fm.match = event.match
        fm.command = pyof.OFPFC_ADD
        fm.idle_timeout = 5
        fm.buffer_id = event.pktin.buffer_id
        self.conn.db[event.sock].send(fm.pack())

        output.vdbg("Dropping flow with match "+\
                        event.match.show().replace('\n',';'))

        #Do not need to check for buffer_id == -1, since we are
        #dropping packets

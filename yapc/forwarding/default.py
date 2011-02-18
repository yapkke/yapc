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
import yapc.forwarding.flows as flows

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
            flow = flows.exact_entry(event.match)
            flow.add_output(pyof.OFPP_FLOOD)
           
            if (event.pktin.buffer_id == flows.UNBUFFERED_ID):
                self.conn.db[event.sock].send(flow.get_packet_out().pack()+event.pkt)
                output.vdbg("Flood unbuffered packet with match "+\
                                event.match.show().replace('\n',';'))
            else:
                po.buffer_id = event.pktin.buffer_id
                self.conn.db[event.sock].send(flow.get_packet_out().pack())
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
                self.conn.db[event.sock].send(fm.get_flow_mod(pyof.OFPFC_ADD).pack())

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
            flow = flows.exact_entry(event.match)
            self.conn.db[event.sock].send(flow.get_flow_mod().pack())
            output.vdbg("Dropping flow with match "+\
                            event.match.show().replace('\n',';'))

        return True

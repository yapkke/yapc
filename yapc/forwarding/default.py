##Default forwarding actions
#
# Some forwarding ways of handling unhandled packets
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.log.output as output
import yapc.events.openflow as ofevents
import yapc.pyopenflow as pyof
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
            flow.set_buffer(event.pktin.buffer_id)
            flow.add_output(pyof.OFPP_FLOOD)
           
            if (event.pktin.buffer_id == flows.UNBUFFERED_ID):
                self.conn.send(event.sock, flow.get_packet_out().pack()+event.pkt)
                output.vdbg("Flood unbuffered packet with match "+\
                                event.match.show().replace('\n',';'))
            else:
                self.conn.send(event.sock,flow.get_packet_out().pack())
                output.vdbg("Flood buffered packet with match "+\
                                event.match.show().replace('\n',';'),
                            self.__class__.__name__)
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

    def add_perm(self, flowentry):
        """Add permanent flow entry to install
        """
        flowentry.idle_timeout = pyof.OFP_FLOW_PERMANENT
        flowentry.hard_timeout = pyof.OFP_FLOW_PERMANENT
        self.entries.append(flowentry)

    def add_perm_output(self, flowentry, port=pyof.OFPP_CONTROLLER,
                        max_len=pyof.OFP_DEFAULT_MISS_SEND_LEN):
        """Add permanent flow entry to install with output action appended
        """
        flowentry.add_output(port, max_len)
        self.add_perm(flowentry)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        """
        if (isinstance(event, ofevents.features_reply)):
            for fm in self.entries:
                self.conn.send(event.sock,fm.get_flow_mod(pyof.OFPFC_ADD).pack())

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
            flow.set_buffer(event.pktin.buffer_id)
            self.conn.send(event.sock,flow.get_flow_mod(pyof.OFPFC_ADD).pack())
            output.vdbg("Dropping flow with match "+\
                            event.match.show().replace('\n',';'))

        return True

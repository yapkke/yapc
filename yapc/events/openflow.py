##Generic OpenFlow events
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.log.output as output
import yapc.comm.openflow as ofcomm
import yapc.pyopenflow as pyof
import yapc.util.openflow as ofutil

class action_unpacker:
    """Class that implements functions to unpack actions
    
    @author ykk
    @date Sept 2011
    """
    def unpack_action(self, string):
        """Unpack action
        
        @param string binary string of actions
        @return (action, remaining)
        """
        remaining = string
        action = None

        ah = pyof.ofp_action_header()
        ah.unpack(string)
        if (ah.type == pyof.OFPAT_OUTPUT):
            action = pyof.ofp_action_output()
            remaining = action.unpack(string)
        else:
            output.warn("Unhandled action type "+str(ah.type)+"!",
                        self.__class__.__name__)
            return (None, remaining[ah.len:])

        return (action, remaining)

    def unpack_actions(self, string, actions=None):
        """Unpack actions

        @param string string with actions encoded
        @param actions list to add actions into
        @return list of actions
        """
        remaining = string
        if (actions == None):
            actions = []

        while (len(remaining) >= pyof.OFP_ACTION_HEADER_BYTES):
            (action, remaining) = self.unpack_action(remaining)
            actions.append(action)
        
        if (len(remaining) > 0):
            output.warn("Action array is of irregular length with "+\
                            str(len(remaining))+" bytes remaining.",
                        self.__class__.__name__)
            
        return actions

class parser(yapc.component):
    """OpenFlow parser that generates OpenFlow events
    
    @author ykk
    @date Feb 2011
    """
    def __init__(self, server):
        """Initialize
        
        @param server yapc core
        """
        ##Reference to scheduler
        self.scheduler = server

        server.register_event_handler(ofcomm.message.name, self)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        """
        if (isinstance(event, ofcomm.message)):
            if (event.header.type == pyof.OFPT_FLOW_REMOVED):
                self.scheduler.post_event(flow_removed(event.sock,
                                                       event.message))

            elif (event.header.type == pyof.OFPT_PACKET_IN):
                self.scheduler.post_event(pktin(event.sock,
                                                event.message))

            elif (event.header.type == pyof.OFPT_ERROR):
                self.scheduler.post_event(error(event.sock,
                                                event.message))

            elif (event.header.type == pyof.OFPT_GET_CONFIG_REPLY):
                self.scheduler.post_event(config_reply(event.sock,
                                                       event.message))

            elif (event.header.type == pyof.OFPT_FEATURES_REPLY):
                self.scheduler.post_event(features_reply(event.sock,
                                                         event.message))

            elif (event.header.type == pyof.OFPT_PORT_STATUS):
                self.scheduler.post_event(port_status(event.sock,
                                                      event.message))

            elif (event.header.type == pyof.OFPT_STATS_REPLY):
                self.handle_stats_reply(event)

        return True

    def handle_stats_reply(self, event):
        """Handle stats reply
        """
        stats_reply = pyof.ofp_stats_reply()
        reply = stats_reply.unpack(event.message)
        if (stats_reply.type == pyof.OFPST_FLOW):
            self.scheduler.post_event(flow_stats(event.sock,
                                                 event.message,
                                                 stats_reply, reply))

class error(ofcomm.message):
    """Error in OpenFlow

    @author ykk
    @date Feb 2011
    """
    name = "OpenFlow Port Status"
    def __init__(self, sock, msg):
        """Initialize

        @param sock reference to socket
        @param msg message
        """
        ofcomm.message.__init__(self, sock, msg)

        ##Error
        self.error = None

        if (self.header.type == pyof.OFPT_ERROR):
            self.error = pyof.ofp_error_msg()
            self.error.unpack(msg)

class port_status(ofcomm.message):
    """Port status in OpenFlow

    @author ykk
    @date Feb 2011
    """
    name = "OpenFlow Port Status"
    def __init__(self, sock, msg):
        """Initialize

        @param sock reference to socket
        @param msg message
        """
        ofcomm.message.__init__(self, sock, msg)

        ##Port status
        self.port = None

        if (self.header.type == pyof.OFPT_PORT_STATUS):
            self.port = pyof.ofp_port_status()
            self.port.unpack(msg)

class config_reply(ofcomm.message):
    """Switch config in OpenFlow

    @author ykk
    @date Mar 2011
    """
    name = "OpenFlow Switch Config Reply"
    def __init__(self, sock, msg):
        """Initialize

        @param sock reference to socket
        @param msg message
        """
        ofcomm.message.__init__(self, sock, msg)

        ##Switch config struct
        self.config = None

        if (self.header.type == pyof.OFPT_GET_CONFIG_REPLY):
            self.config = pyof.ofp_switch_config()
            r = self.config.unpack(msg)
            if (len(r) > 0):
                output.warn("Config reply is of irregular length with "+\
                                str(len(r))+" bytes remaining.",
                            self.__class__.__name__)
            output.dbg("Received switch config:\n"+\
                           self.config.show("\t"),
                       self.__class__.__name__)

class features_reply(ofcomm.message):
    """Features reply event in OpenFlow

    @author ykk
    @date Feb 2011
    """
    name = "OpenFlow Features Reply"
    def __init__(self, sock, msg):
        """Initialize

        @param sock reference to socket
        @param msg message
        """
        ofcomm.message.__init__(self, sock, msg)

        ##Features struct
        self.features = None
        
        if (self.header.type == pyof.OFPT_FEATURES_REPLY):
            self.features = pyof.ofp_switch_features()
            r = self.features.unpack(msg)
            while (len(r) >= pyof.OFP_PHY_PORT_BYTES):
                p = pyof.ofp_phy_port()
                r = p.unpack(r)
                self.features.ports.append(p)
            if (len(r) > 0):
                output.warn("Features reply is of irregular length with "+\
                                str(len(r))+" bytes remaining.",
                            self.__class__.__name__)
            output.dbg("Received switch features:\n"+\
                           self.features.show("\t"),
                       self.__class__.__name__)

class flow_removed(ofcomm.message):
    """Flow removed event in OpenFlow
    
    @author ykk
    @date May 2011
    """
    name = "OpenFlow Flow Removed"
    def __init__(self, sock, msg):
        """Initialize

        @param sock reference to socket
        @param msg message
        """
        ofcomm.message.__init__(self, sock, msg)

        ##Flow removed 
        self.flowrm = None

        if (self.header.type == pyof.OFPT_FLOW_REMOVED):
            self.flowrm = pyof.ofp_flow_removed()
            self.flowrm.unpack(msg)

class pktin(ofcomm.message):
    """Packet in event in OpenFlow

    @author ykk
    @date Feb 2011
    """
    name = "OpenFlow Packet In"
    def __init__(self, sock, msg):
        """Initialize

        @param sock reference to socket
        @param msg message
        """
        ofcomm.message.__init__(self, sock, msg)

        ##Packet in header
        self.pktin = None
        ##Packet included parsed by dpkt
        self.dpkt = None
        ##Binary packet
        self.pkt = None
        ##Exact match for match
        self.match = None

        if (self.header.type == pyof.OFPT_PACKET_IN):
            self.pktin = pyof.ofp_packet_in()
            self.pkt = self.pktin.unpack(msg)
            output.vdbg("Packet in\n"+self.pktin.show("\t"),
                        self.__class__.__name__)
            (self.match, self.dpkt) = ofutil.get_ofp_match(self.pktin.in_port, 
                                                           self.pkt)
            output.vdbg("Packet has match\n"+self.match.show("\t"),
                        self.__class__.__name__)
            output.vdbg(str(`self.dpkt`),
                        self.__class__.__name__)
    
class flow_stats(ofcomm.message, action_unpacker):
    """Flow stats in OpenFlow

    @author ykk
    @date Sept 2011
    """
    name = "OpenFlow Flow Stats Reply"
    def __init__(self, sock, msg, stats_reply=None, reply=None):
        """Initialize

        @param sock reference to socket
        @param msg message
        """
        ofcomm.message.__init__(self, sock, msg)

        ##Stats reply header
        self.stats_reply = stats_reply
        
        remaining = reply
        if (self.stats_reply == None) or (remaining == None):
            self.stats_reply = pyof.ofp_stats_reply()
            remaining = self.stats_reply.unpack(msg)
        
        ##Flow stats of individual flows
        self.flows = []
        while (len(remaining) >= pyof.OFP_FLOW_STATS_BYTES):
            flow = pyof.ofp_flow_stats()
            flow.unpack(remaining)
            self.unpack_actions(remaining[pyof.OFP_FLOW_STATS_BYTES:flow.length], flow.actions)
            remaining = remaining[flow.length:]
            self.flows.append(flow)

        if (len(remaining) > 0):
            output.warn("Flow stats reply is of irregular length with "+\
                            str(len(remaining))+" bytes remaining.",
                        self.__class__.__name__)
        output.vdbg("Received "+str(len(self.flows))+" flow stats.",
                   self.__class__.__name__)

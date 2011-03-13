##Generic OpenFlow events
#
# 
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.output as output
import yapc.ofcomm as ofcomm
import yapc.pyopenflow as pyof
import yapc.openflowutil as ofutil

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
            if (event.header.type == pyof.OFPT_PACKET_IN):
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

        return True

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
    
        

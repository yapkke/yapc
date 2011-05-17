##Topology discovery and maintenance
#
# @author ykk
# @date Feb 2011
#
import struct
import time
import dpkt.ethernet
import yapc.interface as yapc
import yapc.events.openflow as ofevents
import yapc.events.network as netevents
import yapc.packet.lldp as lldppkt
import yapc.netstate.switches as swstate
import yapc.util.memcacheutil as mc
import yapc.pyopenflow as pyof
import yapc.util.openflow as ofutil
import yapc.util.parse as parseutil
import yapc.log.output as output

class link_maintain:
    """Class that maintain link and timeout

    @author ykk
    @date Feb 2011
    """
    def __init__(self, server, timeout):
        """Initialize
        """
        ##Reference to server
        self.server = server
        ##Time to wait before timing out link
        self.timeout = timeout
        ##List of time
        self.__expiration = []
        self.__links = []
        
        mc.get_client()
        

    def update(self, src_dpid, src_port, dst_dpid, dst_port):
        """Update link
        """
        link = (src_dpid, src_port, dst_dpid, dst_port)
        try:
            index = self.__links.index(link)
            self.__expiration.pop(index)
            self.__links.pop(index)
        except ValueError:
            self.server.post_event(netevents.link_up(link[0], link[1],
                                                     link[2], link[3]))
        self.__expiration.append(time.time()+self.timeout)
        self.__links.append(link)
        self.check_expire

    def check_expire(self):
        """Expire outdated links
        """
        while (len(self.__expiration) > 0 and
               (self.__expiration[0] < time.time())):
            #Expired link
            link = self.__links.pop(0)
            self.__expiration.pop(0)
            self.server.post_event(netevents.link_down(link[0], link[1],
                                                       link[2], link[3]))
        
class lldp_link_discovery(yapc.component):
    """Discover links using LLDP

    Sends LLDP at regular intervals.

    @author ykk
    @date Feb 2011
    """
    def __init__(self, server, ofconn,
                 sendinterval=10, linktimeout=30):
        """Initialize

        @param server yapc core
        """
        if (sendinterval > linktimeout):
            output.warn("Probe interval of "+str(sendinterval)+\
                        "is smaller than timeout of "+str(linktimeout),
                        self.__class__.__name__)
        ##Interval to send LLDP per switch/port
        self.interval = sendinterval
        self.__minterval = sendinterval
        ##Time to wait before timing out link
        self.link_maintain = link_maintain(server, linktimeout)
        ##Reference to core
        self.server = server
        ##Reference to OpenFlow connections
        self.conn = ofconn
        ##Current list of switch/port LLDP is sent
        self.__sw_port = []
        ##Packet out template
        self.__po = pyof.ofp_packet_out()
        oao = pyof.ofp_action_output()
        self.__po.in_port = pyof.OFPP_NONE
        self.__po.actions_len = oao.len
        self.__po.actions.append(oao)

        mc.get_client()

        server.register_event_handler(ofevents.pktin.name,
                                      self)
        server.register_event_handler(ofevents.port_status.name,
                                      self)
        server.register_event_handler(ofevents.features_reply.name,
                                      self)
        server.post_event(yapc.priv_callback(self, True),
                          self.interval)

    def processevent(self, event):
        """Handle event
        """
        if isinstance(event, ofevents.pktin):
            #Check for LLDP and discover/maintain links
            if (event.dpkt.type == lldppkt.LLDP_ETH):
                lldp = lldppkt.LLDP(event.dpkt.data)
                src_dpid = int(lldp.value[1:], 16)
                src_port = int(lldp.data.value[1:])
                dst_dpid = self.conn.db[event.sock].dpid
                dst_port = event.pktin.in_port
                self.link_maintain.update(src_dpid, src_port,
                                          dst_dpid, dst_port)
                output.vdbg("%x:" % dst_dpid + str(dst_port)+\
                            " receive LLDP packet from %x" % src_dpid+\
                            ":"+str(src_port),
                            self.__class__.__name__)
                
                return False
        
        elif isinstance(event, ofevents.port_status):
            #New port, so let's try to find a new link fast
            self.send_lldp(self.conn.db[event.sock].dpid,
                           event.port.desc)

        elif isinstance(event, ofevents.features_reply):
            #New switch, so let's try to find new links fast
            for p in event.features.ports:
                self.send_lldp(event.features.datapath_id, p)

        elif isinstance(event, yapc.priv_callback):
            if (event.magic ==True):
                #Periodic enumeration of switch port to maintain
                dpidsl = mc.get(swstate.dp_features.DP_SOCK_LIST)
                if (dpidsl != None):
                    for key in dpidsl:
                        sw = mc.get(key)
                        for p in sw.ports:
                            if (p.port_no <= pyof.OFPP_MAX and
                                (sw.datapath_id, p) not in self.__sw_port):
                                self.__sw_port.append((sw.datapath_id, p))
                    if (len(self.__sw_port) != 0):
                        self.__minterval = float(self.interval)/len(self.__sw_port)
                        self.server.post_event(yapc.priv_callback(self, False),0)
                    output.vdbg("Gather "+str(len(self.__sw_port))+" to send LLDP to",
                               self.__class__.__name__)
                else:
                    output.dbg("No switch port to send LLDP to",
                               self.__class__.__name__)
                self.server.post_event(yapc.priv_callback(self, True),
                                  self.interval)
            else:
                #Sending of LLDP for maintenance
                if (len(self.__sw_port) > 0):
                    (sw,port) = self.__sw_port.pop()
                    self.send_lldp(sw, port)
                    self.server.post_event(yapc.priv_callback(self, False),
                                           self.__minterval)
                self.link_maintain.check_expire()
                
        return True

    def send_lldp(self, sw, port):
        """Send LLDP to switch and port

        @param sw datapath id of switch
        @param port phy port
        """
        self.__po.xid = ofutil.get_xid()
        self.__po.actions[0].port = port.port_no
        switch = self.conn.get_conn(sw)
        if (switch != None):
            switch.send(self.__po.pack()+\
                        self.form_eth_lldp(sw, port))
            output.vdbg("Sending LLDP to %x:" % sw +str(port.port_no),
                        self.__class__.__name__)

    def form_eth_lldp(self, sw, port):
        """Form Ethernet packet with switch and port

        @param sw datapath id of switch
        @param port phy port
        """
        lldpttl = lldppkt.LLDP_TLV()
        lldpttl.type = 3
        lldpttl.value = struct.pack('>H',60)
        lldpttl.data = lldppkt.LLDP_TLV()
        
        lldpport = lldppkt.LLDP_TLV()
        lldpport.type = 2
        lldpport.value = '\x07'+"%x" % port.port_no
        lldpport.data = lldpttl

        lldpchasis = lldppkt.LLDP()
        lldpchasis.type = 1
        lldpchasis.value = '\x07'+"%x" % sw
        lldpchasis.data = lldpport

        ethpkt = dpkt.ethernet.Ethernet()
        ethpkt.src = parseutil.array2byte_str(port.hw_addr)
        ethpkt.dst = '\x01\x80\xc2\x00\x00\x0e'
        ethpkt.type = lldppkt.LLDP_ETH
        ethpkt.data = lldpchasis.pack()
        
        return ethpkt.pack()

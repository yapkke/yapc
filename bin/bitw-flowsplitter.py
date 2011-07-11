#!/usr/bin/env python
import yapc.core as core
import yapc.log.output as output
import yapc.interface as yapc
import yapc.local.netintf as neti
import yapc.local.packetprocessor as pp
import yapc.util.parse as pu
import sys
import getopt
import dpkt
import socket

class flowsplitter(pp.bitw):
    """A base class for Bump-in-the-wire
    
    @author ykk
    @date July 2011
    """
    def __init__(self, server, intf, extintf, ip):
        """Initialize

        @param server reference to yapc core
        @param intf name of interface to attach bump in the wire
        @param extintf name of external interface to attach bump in the wire
        @param ip list of destination IP to use (first being the primary one)
        """
        pp.bitw.__init__(self, server, intf, extintf)
        self.extintf = extintf
        self.ip = []
        for i in ip:
            self.ip.append(pu.ip_string2binary(i))
        self.__index = 0
        output.info("Setting up flow splitter from "+extintf+" to "+intf+\
                        " for splitting flow among "+str(self.ip),
                    self.__class__.__name__)


    def process(self, packet, intf):
        """Process packet
        """
        pkt = dpkt.ethernet.Ethernet(packet)
        if ((pkt["type"] == dpkt.ethernet.ETH_TYPE_IP) and
            (pkt["data"]["dst"] == self.ip[0]) and
            (pkt["data"]["p"] == 6)):

            setattr(pkt["data"], "dst", self.ip[self.__index])
            setattr(pkt["data"], "sum", 0)
            setattr(pkt["data"]["data"], "sum", 0)

            self.__index += 1
            if (self.__index >= len(self.ip)):
                self.__index = 0

            return pkt.pack()
        else:
            return packet

class bitw_flowsplitter(yapc.daemon):
    def __init__(self):
        yapc.daemon.__init__(self)
        ##External interface
        self.extintf = "eth1"
        ##IP to send to
        self.ip = []
        ##Internal interface
        self.__intf = None

    def configure_if(self, intfmgr):
        intfmgr.set_ipv4_addr(self.extintf, "0.0.0.0")
        
        intfmgr.add_veth()
        intfmgr.set_eth_addr(intfmgr.veth[0].names[1],
                             intfmgr.ethernet_addr(self.extintf))
        self.__intf = intfmgr.veth[0].names[1]
        intfmgr.up(intfmgr.veth[0].names[0])

    def run(self):
        server = core.core()
        intfmgr=neti.interfacemgr(server)

        self.configure_if(intfmgr)
        fs = flowsplitter(server, self.extintf,
                          intfmgr.veth[0].names[0], 
                          self.ip)
        server.run()
        sys.exit(0)

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" ext_interface dst_ip_1 dst_ip_2 ..."
    print "\tBump-in-the-wire (TCP flow splitter)"
    print "\tSplit TCP flow to destination in a round-robin manner"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-v/--verbose\n\tVerbose output"
    print "--very-verbose\n\tVery verbose output"
    print "-d/--daemon\n\tRun as daemon"

bfs = bitw_flowsplitter()
output.set_mode("INFO")

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvd",
                               ["help","verbose","daemon", 
                                "very-verbose"])
except getopt.GetoptError:
    print "Option error!"
    usage()
    sys.exit(2)

#Parse options
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-v","--verbose")):
        output.set_mode("DBG")
    elif (opt in ("--very-verbose")):
        output.set_mode("VDBG")
    elif (opt in ("-d","--daemon")):
        bfs.daemon=True
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

bfs.extintf = args[0]
bfs.ip = args[1:]

bfs.start()

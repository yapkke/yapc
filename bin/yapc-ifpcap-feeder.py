#!/usr/bin/env python
import yapc.core as core
import yapc.log.output as output
import yapc.interface as yapc
import yapc.packet.source as pktsrc
import yapc.comm.raw as rcomm
import sys
import getopt
import dpkt
import pcap

class ifpcap_feeder(yapc.daemon):
    def __init__(self):
        yapc.daemon.__init__(self)
        ##Interface
        self.intf = None
        ##pcap file
        self.pcap = None

    def inject_packet(self, rs, packet):
        rs.send(packet)
        p = dpkt.ethernet.Ethernet(packet)
        output.dbg(`p`, self.__class__.__name__)

    def run(self):
        server = core.core()

        pf = pktsrc.pcap_file(self.pcap)
        rs = rcomm.rawsocket(server, self.intf)

        pkt = pf.get_next()
        while (pkt != None):
            self.inject_packet(rs, pkt[1])
            pkt = pf.get_next()

        server.cleanup()
        sys.exit(0)

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" interface pcap_file"
    print "\tInterface pcap feeder"
    print "\tFeeds packet in pcap file into interface"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-v/--verbose\n\tVerbose output"
    print "--very-verbose\n\tVery verbose output"
    print "-d/--daemon\n\tRun as daemon"

ipf = ifpcap_feeder()
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

if (len(args) < 2):
    print "Insufficient arguments!"
    usage()
    sys.exit(2)

ipf.intf = args[0]
ipf.pcap = args[1]
ipf.start()


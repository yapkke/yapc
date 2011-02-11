#!/usr/bin/env python

import yapc.output as output
import yapc.openflowutil as ofutil
import pcap
import dpkt
import sys

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" [options] <file name>"
    print "\tpcap file should contain OpenFlow packet-in's"
    print
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "h",
                               ["help"])
except getopt.GetoptError:
    print "Option error!"
    usage()
    sys.exit(2)

#Parse options
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

if (len(args) < 1):
    print "Missing filename"
    usage()
    sys.exit(2)

output.set_mode("DBG")
pc = pcap.pcap(args[0])
for ts,pkt in pc:
    dpktpkt = dpkt.ethernet.Ethernet(pkt)
    output.dbg(str(`dpktpkt`))
    ofdata = dpktpkt["data"]["data"]["data"]
    (ofm, dpktp) = ofutil.get_ofp_match(0, ofdata[18:])
    output.dbg(str(`dpktp`))
    output.dbg("OFP MATCH\n"+ofm.show())

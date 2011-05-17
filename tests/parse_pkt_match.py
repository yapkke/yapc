#!/usr/bin/env python

import yapc.log.output as output
import yapc.util.openflow as ofutil
import pcap
import dpkt
import sys
import getopt

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" [options] <file name>"
    print "\tpcap file should contain packets for parsing"
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
for ts,ofdata in pc:
    (ofm, dpktp) = ofutil.get_ofp_match(0, ofdata)
    output.dbg(str(`dpktp`))
    output.dbg("OFP MATCH\n"+ofm.show())

#!/usr/bin/python
## Client OpenFlow Interface for Networking (Bridge)
# @author ykk
# @date Aug 2011
#
import yapc.core as core
import yapc.interface as yapc
import yapc.comm.openflow as ofcomm
import yapc.events.openflow as ofevents
import yapc.log.output as output
import sys
import getopt

class coin_bridge(yapc.daemon):
    def __init__(self):
        yapc.daemon.__init__(self)
        ##Interfaces to add
        self.interfaces = []

    def run(self):
        server = core.core()
        ofconn = ofcomm.ofserver(server)

        #OpenFlow Parser
        ofparse = ofevents.parser(server)

        server.run()
        sys.exit(0)

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" [options] command <parameters>"
    print "\tCOIN bridge"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-v/--verbose\n\tVerbose output"
    print "--vs\n\tVerbose output for selected component"
    print "--very-verbose\n\tVery verbose output"
    print "-d/--daemon\n\tRun as daemon"
    print "-i/--interface\n\tSpecify interface to add"

coinb = coin_bridge()

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvdi:",
                               ["help","verbose","daemon", 
                                "very-verbose","vs=", "interface="])
except getopt.GetoptError:
    print "Option error!"
    usage()
    sys.exit(2)

output.set_mode("INFO")

#Parse options
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-v","--verbose")):
        output.set_mode("DBG")
    elif (opt in ("--vs")):
        output.set_mode("DBG", arg)
    elif (opt in ("--very-verbose")):
        output.set_mode("VDBG")
    elif (opt in ("-d","--daemon")):
        coinb.daemon=True
    elif (opt in ("-i","--interface")):
        coinb.interfaces.append(arg)
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

if (coinb.daemon):
    output.set_logfile('/var/log/coin.log')
coinb.start()

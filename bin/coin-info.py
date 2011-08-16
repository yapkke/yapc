#!/usr/bin/env python
import yapc.core as core
import yapc.interface as yapc
import yapc.log.output as output
import yapc.comm.json as jsoncomm
import yapc.coin.information as coini
import yapc.coin.core as coin
import yapc.local.networkstate as ns
import sys
import getopt

class coin_info(yapc.daemon):
    def __init__(self):
        yapc.daemon.__init__(self)
        self.server = core.core()
        self.coin = coini.core(self.server)
        ##Force JSON connection or not
        self.forcejson = False
        ##Socket to talk to
        self.sock = coin.SOCK_NAME

    def run(self):
        jsonconn = jsoncomm.jsonserver(self.server, file=self.sock, 
                                       forcebind=self.forcejson)
        coininfoj = coini.jsonquery(self.server, jsonconn.connections)
        bwm = ns.coin_intf_bandwidth(self.coin)

        self.coin.start()
        self.server.run()

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" [options]"
    print "\tIndependent information plane for COIN"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-v/--verbose\n\tVerbose output"
    print "--very-verbose\n\tVery verbose output"
    print "-f/--force-json\n\tForced binding for JSON UNIX socket"
    print "-s/--sock\n\tSocket to communicate to (default: "+coin.SOCK_NAME+")"

output.set_mode("DBG")
ci = coin_info()

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvs:f",
                               ["help","verbose", "very-verbose", "sock=", "force-json"])
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
    elif (opt in ("-s","--sock")):
        ci.sock = arg
    elif (opt in ("-f","--force-json")):
        ci.forcejson=True
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

ci.start()

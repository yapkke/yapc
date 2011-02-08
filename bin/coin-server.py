#!/usr/bin/python
## Client OpenFlow Interface for Networking
# @author ykk
# @date Oct 2010
#
import yapc.core as core
import yapc.interface as yapc
import yapc.ofcomm as ofcomm
import yapc.jsoncomm as jsoncomm
import yapc.output as output
import yapc.coin.core as coin
import yapc.coin.ovs as coinovs
import yapc.netstate.switches as switches
import yapc.forwarding.default as default
import sys
import getopt


class coin_server(yapc.daemon):
    def __init__(self):
        yapc.daemon.__init__(self)
        ##Verbose debug output or not
        self.debug = "INFO"
        ##Force JSON connection or not
        self.forcejson = False
        ##Socket to talk to
        self.sock = coin.SOCK_NAME

    def run(self):
        """Run server
        """
        #Configure logging
        output.set_mode(self.debug)

        #Create yapc base
        server = core.server()
        ofcomm.ofserver().bind(server)
        jsoncomm.jsonserver(file=self.sock, 
                            forcebind=self.forcejson).bind(server)

        #COIN main server, maintaining connections
        coinserver = coin.server(server)
        #Network status
        sw = switches.dp_features(server)
        #OVS fabric manager
        ovs = coinovs.switch(server, coinserver)

        #Drop unhandled flows
        df = default.dropflow(server, coinserver)
        
        server.run()
        
        sys.exit(0)
        
##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" [options] command <parameters>"
    print "\tCOIN server"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-f/--force-json\n\tForced binding for JSON UNIX socket"
    print "-s/--sock\n\tSocket to communicate to (default: "+coin.SOCK_NAME+")"
    print "-v/--verbose\n\tVerbose output"
    print "--very-verbose\n\tVery verbose output"
    print "-d/--daemon\n\tRun as daemon"

coins = coin_server()

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvdfs:",
                               ["help","verbose","daemon", 
                                "very-verbose",
                                "force-json","sock="])
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
        coins.debug="DBG"
    elif (opt in ("--very-verbose")):
        coins.debug="VDBG"
    elif (opt in ("-d","--daemon")):
        coins.daemon=True
    elif (opt in ("-s","--sock")):
        coins.sock = arg
    elif (opt in ("-f","--force-json")):
        coins.forcejson=True
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

coins.start()

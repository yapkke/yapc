#!/usr/bin/python
## Client OpenFlow Interface for Networking (Indirection)
# @author ykk
# @date Aug 2011
#
import yapc.core as core
import yapc.interface as yapc
import yapc.coin.core as coin
import yapc.coin.bridge as coinbr
import yapc.coin.ovs as coinovs
import yapc.comm.openflow as ofcomm
import yapc.comm.json as jsoncomm
import yapc.comm.udpjson as udpjson
import yapc.events.openflow as ofevents
import yapc.netstate.switches as switches
import yapc.log.output as output
import sys
import getopt

class coin_indirection(yapc.daemon):
    def __init__(self):
        yapc.daemon.__init__(self)
        ##Interfaces to add
        self.interfaces = []
        ##Force JSON connection or not
        self.forcejson = False
        ##Socket to talk to
        self.sock = coin.SOCK_NAME
        ##UDP port
        self.port = udpjson.SOCK_PORT

    def run(self):
        server = core.core()
        ofconn = ofcomm.ofserver(server)
        jsonconn = jsoncomm.jsonserver(server, file=self.sock, 
                                       forcebind=self.forcejson)
        ujson = udpjson.jsonudpserver(server, self.port)

        #OpenFlow Parser
        ofparse = ofevents.parser(server)
        #COIN main sever, maintaining connection
        coinserver = coinbr.bridge(server, ofconn.connections, 
                                   jsonconn.connections)

        #Network status
        sw = switches.dp_features(server)

        #OVS fabric manager
        ovs = coinovs.switch(server, jsonconn.connections)
        coinserver.switch = ovs

        #Flow management
        trafh = coinbr.traffic_handler(server, ofconn.connections, coinserver)

        #Add interfaces
        coinserver.setup(self.interfaces)

        server.order_handler(ofevents.features_reply.name,
                             sw, coinserver)
        server.order_cleanup(ofconn, ovs)

        server.run()
        sys.exit(0)

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" [options] command <parameters>"
    print "\tCOIN indirection"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-v/--verbose\n\tVerbose output"
    print "--vs\n\tVerbose output for selected component"
    print "--very-verbose\n\tVery verbose output"
    print "-d/--daemon\n\tRun as daemon"
    print "-f/--force-json\n\tForced binding for JSON UNIX socket"
    print "-s/--sock\n\tSocket to communicate to (default: "+coin.SOCK_NAME+")"
    print "-i/--interface\n\tSpecify interface to add"

coinb = coin_indirection()

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvdi:s:f",
                               ["help","verbose","daemon", 
                                "very-verbose","vs=", "interface=",
                                "sock=","force-json"])
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
    elif (opt in ("-f","--force-json")):
        coinb.forcejson=True
    elif (opt in ("-s","--sock")):
        coinb.sock = arg
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

if (coinb.daemon):
    output.set_logfile('/var/log/coin.log')
coinb.start()

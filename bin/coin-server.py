#!/usr/bin/python
## Client OpenFlow Interface for Networking
# @author ykk
# @date Oct 2010
#
import yapc.core as core
import yapc.ofcomm as ofcomm
import yapc.jsoncomm as jsoncomm
import yapc.output as output
import yapc.coin.core as coin
import yapc.coin.ovs as coinovs
import yapc.netstate.switches as switches
import yapc.forwarding.default as default
import sys
import getopt

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
##Verbose debug output or not
debug = "INFO"
##Run as daemon
daemon = False
##Force JSON connection or not
forcejson = False
##Socket to talk to
sock = coin.SOCK_NAME
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-v","--verbose")):
        debug="DBG"
    elif (opt in ("--very-verbose")):
        debug="VDBG"
    elif (opt in ("-d","--daemon")):
        daemon=True
    elif (opt in ("-s","--sock")):
        sock = arg
    elif (opt in ("-f","--force-json")):
        forcejson=True
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

#Configure logging
if (daemon):
    output.set_daemon_log()
output.set_mode(debug)

#Create yapc base
server = core.server()
ofcomm.ofserver().bind(server)
jsoncomm.jsonserver(file=sock, forcebind=forcejson).bind(server)

#COIN main server, maintaining connections
coinserver = coin.server()
server.scheduler.registereventhandler(ofcomm.message.name,
                                      coinserver)
server.scheduler.registereventhandler(jsoncomm.message.name,
                                      coinserver)

#Network status
sw = switches.dp_features()
server.scheduler.registereventhandler(ofcomm.message.name, sw)

#OVS fabric manager
ovs = coinovs.switch(coinserver)
server.scheduler.registereventhandler(jsoncomm.message.name, ovs)
server.scheduler.registereventhandler(ofcomm.message.name, ovs)
server.scheduler.registercleanup(ovs)

#Drop unhandled flows
df = default.dropflow(coinserver)
server.scheduler.registereventhandler(ofcomm.message.name, df)

#Start
if (daemon):
    server.daemonize()
else:
    server.run()
sys.exit(0)

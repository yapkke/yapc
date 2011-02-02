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
import yapc.coin.bond as coinbond
import yapc.coin.ipupbond as coinipupbond
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
    print "-v/--verbose\n\tVerbose output"
    print "-d/--daemon\n\tRun as daemon"

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvdf",
                               ["help","verbose","daemon", "force-json"])
except getopt.GetoptError:
    print "Option error!"
    usage()
    sys.exit(2)

#Parse options
##Verbose debug output or not
debug = False
##Run as daemon
daemon = False
##Force JSON connection or not
forcejson = False
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-v","--verbose")):
        debug=True
    elif (opt in ("-d","--daemon")):
        daemon=True
    elif (opt in ("-f","--force-json")):
        forcejson=True
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

#Set output mode
if (debug):
    output.set_mode("DBG")
else:
    output.set_mode("INFO")

#Create yapc base
server = core.server()
ofcomm.ofserver().bind(server)
jsoncomm.jsonserver(file="coin.sock", forcebind=forcejson).bind(server)

#COIN main server
coinserver = coin.server()
server.scheduler.registereventhandler(ofcomm.message.name,
                                      coinserver)
server.scheduler.registereventhandler(jsoncomm.message.name,
                                      coinserver)



#coinbond = coinbond.handler(coinserver)
#coinipupbond = coinipupbond.handler(coinserver)
#server.scheduler.registereventhandler(jsoncomm.message.name,
#                                      coinbond)
#server.scheduler.registereventhandler(ofcomm.message.name,
#                                      coinbond)
#server.scheduler.registereventhandler(jsoncomm.message.name,
#                                      coinipupbond)
#server.scheduler.registereventhandler(ofcomm.message.name,
#coinipupbond)

#Start
if (daemon):
    server.daemonize()
else:
    server.run()
sys.exit(0)

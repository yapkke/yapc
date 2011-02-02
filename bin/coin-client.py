#!/usr/bin/env python
## Client OpenFlow Interface for Networking (Client)
# @author ykk
# @date Feb 2011
#
import yapc.jsoncomm as jsoncomm
import yapc.output as output
import simplejson
import sys
import getopt

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" [options] command <parameters>"
    print "\tCreate bonding driver using COIN"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-v/--verbose\n\tVerbose output"
    print  "Commands:"
    print "get_mode\n\tGet current mode of COIN"

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hv",
                               ["help","verbose"])
except getopt.GetoptError:
    print "Option error!"
    usage()
    sys.exit(2)

#Parse options
##Verbose debug output or not
debug = False
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-v","--verbose")):
        debug=True
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

if not (len(args) >= 1):
    print "Missing command!"
    usage()
    sys.exit(2)

#Set output mode
if (debug):
    output.set_mode("DBG")
else:
    output.set_mode("INFO")

#Construct
msg = {}
msg["type"] = "coin"
msg["subtype"] = "mode"
msg["command"] = args[0]

sock = jsoncomm.client("coin.sock")
output.dbg("Sending "+simplejson.dumps(msg),"coin-client")
sock.sock.send(simplejson.dumps(msg))
output.info("Received "+simplejson.dumps(simplejson.loads(sock.sock.recv(1024)),
                                         indent=4))
sys.exit(0)

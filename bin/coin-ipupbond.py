#!/usr/bin/python
## Client OpenFlow Interface for Networking (Bonding)
# @author ykk
# @date Oct 2010
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
    print "create [ip address]\n\tcreate interface to bond other interfaces to"+\
          "for specified IP address"
    print "delete [bond-interface]\n\tcreate interface to bond other interfaces to"
    print "enslave [bond-interface] [interface]\n\tbond interface to bonding interface"
    print "liberate [bond-interface] [interface]\n\tunbond interface to bonding interface"
    print "set-active-slave [bond-interface] [interface]\n\tset interface as active slave "+\
        "to bonding interface"
    print "get-active-slave [bond-interface]\n\tget interface as active slave "+\
        "to bonding interface"

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

if not (len(args) >= 2):
    if (args[0] != "create"):
        print "Missing IP address"
    else:
        print "Missing bond-interface"
    usage()
    sys.exit(2)

if (args[0] != "create") and (args[0] != "delete") and \
        (args[0] != "get-active-slave"):
    if not (len(args) >= 3):
        print "Missing interface"
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
msg["subtype"] = "ipupbond"
msg["command"] = args[0]
if (args[0] != "create"):
    msg["bond-interface"] = args[1]
else:
    msg["ip-address"] = args[1]
if (args[0] != "create") and (args[0] != "delete"):
    msg["interface"] = args[2]

sock = jsoncomm.client()
output.dbg("Sending "+simplejson.dumps(msg),"coin-bond")
sock.sock.send(simplejson.dumps(msg))
output.info("Recevied "+simplejson.dumps(simplejson.loads(sock.sock.recv(1024)),
                                         indent=4))
sys.exit(0)

#!/usr/bin/env python
import yapc.log.output as output
import yapc.comm.json as jsoncomm
import simplejson
import sys
import getopt

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" [options]"
    print "\tFlush SQLite database"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-v/--verbose\n\tVerbose output"
    print "-s/--sock\n\tSocket to communicate to (default: "+coin.SOCK_NAME+")"

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvs:",
                               ["help","verbose","sock="])
except getopt.GetoptError:
    print "Option error!"
    usage()
    sys.exit(2)

#Parse options
##Verbose debug output or not
debug = False
##Socket to talk to
sock = jsoncomm.SOCK_NAME
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-v","--verbose")):
        debug=True
    elif (opt in ("-s","--sock")):
        sock = arg
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

#Set output mode
if (debug):
    output.set_mode("DBG")
else:
    output.set_mode("INFO")

msg = {}
msg["type"] = "sqlite"
msg["command"] = "flush"

sock = jsoncomm.client(sock)
output.dbg("Sending "+simplejson.dumps(msg),"coin-client")
sock.sock.send(simplejson.dumps(msg))
output.info("Received "+simplejson.dumps(simplejson.loads(sock.recv(2048)),
                                         indent=4))

sys.exit(0)

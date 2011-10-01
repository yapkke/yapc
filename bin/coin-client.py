#!/usr/bin/env python
## Client OpenFlow Interface for Networking (Client)
# @author ykk
# @date Feb 2011
#
import yapc.coin.core as coin
import yapc.comm.json as jsoncomm
import yapc.log.output as output
import simplejson
import sys
import getopt

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" [options] command <parameters>"
    print "\tControl COIN switch fabric in host"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-v/--verbose\n\tVerbose output"
    print "-s/--sock\n\tSocket to communicate to (default: "+coin.SOCK_NAME+")"
    print  "Commands:"
    print "get_interfaces\n\tGet current interfaces in datapath/controlled by COIN"
    print "get_eth_interfaces\n\tGet current Ethernet interfaces of device"
    print "add_if [name]\n\tAdd interface to COIN"
    print "del_if [name]\n\tDelete interface from COIN"
    print "create_lo_intf [name]\n\tCreate a new local interface in COIN"
    print "get_all_config\n\tRetrieve all configuration"
    print "get_config [name]\n\tRetrieve configuration with name given"
    print "set_config [name] [value]\n\tConfigure name with value given"
    print "ifconfig [name] [netmask] [ip address] [gateway ip] [gateway mac address]\n\t"+\
        "Assign ip address and gateway to interface"
    print "dhclient [name]\n\tExecute dhclient on interface in COIN"
    print "query [name] [selection] [condition]\n\tExecute SQL query on table of name"+\
        " with selection and condition"

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
sock = coin.SOCK_NAME
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

zero_arg_cmds = ["get_interfaces",
                 "get_eth_interfaces", "get_all_config"]
one_arg_cmds = ["add_if","del_if",
                "create_lo_intf", "dhclient",
                "get_config"]
two_arg_cmds = ["set_config"]
three_arg_cmds = ["query"]
five_arg_cmds = ["ifconfig"]

if (len(args) < 1 or
    ((args[0] not in zero_arg_cmds) and 
     (args[0] not in one_arg_cmds) and
     (args[0] not in two_arg_cmds) and
     (args[0] not in three_arg_cmds) and
     (args[0] not in five_arg_cmds))):
    print "Missing or unknown command!"
    usage()
    sys.exit(2)

if (args[0] in one_arg_cmds):
    if not (len(args) >= 2):
        print "Missing name for interface"
        usage()
        sys.exit(2)

if (args[0] in two_arg_cmds):
    if not (len(args) >= 3):
        print "Missing value"
        usage()
        sys.exit(2)

if (args[0] in three_arg_cmds):
    if not (len(args) >= 4):
        print "Missing values"
        usage()
        sys.exit(2)

if (args[0] in five_arg_cmds):
    if not (len(args) >= 6):
        print "Missing values"
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
msg["command"] = args[0]
if (args[0] == "add_if" or args[0] == "del_if" or
    args[0] == "get_interfaces"):
    msg["subtype"] = "ovs"
elif (args[0] == "create_lo_intf" or args[0] == "dhclient"
      or args[0] == "ifconfig"):
    msg["subtype"] = "loif"
elif (args[0] == "query"):
    msg["subtype"] = "info"
else:
    msg["subtype"] = "global"

if ((args[0] in one_arg_cmds) or 
    (args[0] in two_arg_cmds) or 
    (args[0] in three_arg_cmds) or 
    (args[0] in five_arg_cmds)):
    msg["name"] = args[1]

if (args[0] in two_arg_cmds):
    msg["value"] = args[2]

if (args[0] in three_arg_cmds):
    msg["selection"] = args[2]
    msg["condition"] = args[3]

if (args[0] in five_arg_cmds):
    msg["ipaddr"] = args[2]
    msg["netmask"] = args[3]
    msg["gwaddr"] = args[4]
    msg["gwmac"] = args[5]

sock = jsoncomm.client(sock)
output.dbg("Sending "+simplejson.dumps(msg),"coin-client")
sock.sock.send(simplejson.dumps(msg))
output.info("Received "+simplejson.dumps(simplejson.loads(sock.recv(2048)),
                                         indent=4))
sys.exit(0)

#!/usr/bin/python
## Client OpenFlow Interface for Networking
# @author ykk
# @date Oct 2010
#
import yapc.core as core
import yapc.interface as yapc
import yapc.ofcomm as ofcomm
import yapc.output as output
import yapc.events.openflow as ofevents
import yapc.netstate.swhost as switchhost
import yapc.forwarding.switching as fswitch
import yapc.forwarding.default as default
import yapc.debug.openflow as ofdbg
import sys
import getopt

class flow_switch(yapc.daemon):
    def __init__(self):
        yapc.daemon.__init__(self)
        ##Verbose debug output or not
        self.debug = "INFO"
        ##Port
        self.port = 6633
        
    def run(self):
        """Run server
        """
        #Configure logging
        output.set_mode(self.debug)

        #Create yapc base
        server = core.server()
        ofconn = ofcomm.ofserver(server, self.port)

        #Debugger/Profiler
        #ofcount = ofdbg.of_msg_count(server)

        #OpenFlow Parser
        ofparse = ofevents.parser(server)
        #Switch-host binding
        swhost = switchhost.mac2sw_binding(server)
        #Flow switch
        fsw = fswitch.learningswitch(server, ofconn.connections)
        #Drop unhandled flows
        fp = default.floodpkt(server, ofconn.connections)

        server.run()
        
        sys.exit(0)
        
##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" [options] command <parameters>"
    print "\tyapc's flow switch"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-v/--verbose\n\tVerbose output"
    print "--very-verbose\n\tVery verbose output"
    print "-d/--daemon\n\tRun as daemon"
    print "-p/--port\n\tTCP port to run controller on (default: 6633)"

fs = flow_switch()

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvdp:",
                               ["help","verbose","daemon", 
                                "very-verbose", "port="])
except getopt.GetoptError:
    print "Option error!"
    usage()
    sys.exit(2)

#Parse options
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-p","--port")):
        fs.port = int(arg)
    elif (opt in ("-v","--verbose")):
        fs.debug="DBG"
    elif (opt in ("--very-verbose")):
        fs.debug="VDBG"
    elif (opt in ("-d","--daemon")):
        fs.daemon=True
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

fs.start()

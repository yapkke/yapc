#!/usr/bin/env python
import yapc.core as core
import yapc.log.output as output
import yapc.interface as yapc
import yapc.local.netintf as neti
import yapc.local.packetprocessor as pp
import sys
import getopt

class flowsplitter(pp.bitw):
    """A base class for Bump-in-the-wire
    
    @author ykk
    @date July 2011
    """
    def __init__(self, server, intf, extintf):
        """Initialize

        @param server reference to yapc core
        @param intf name of interface to attach bump in the wire
        @param extintf name of external interface to attach bump in the wire
        """
        pp.bitw.__init__(self, server, intf, extintf)
        output.dbg("Setting up flow splitter from "+extintf+" to "+intf,
                   self.__class__.__name__)

    def processpacket(self, rawmsg):
        """Process packet
 
        Simply send on the other side
        """
        pkt = rawmsg.message
        if (rawmsg.sock == self.intf1.sock):
            self.intf2.sock.send(pkt)
        if (rawmsg.sock == self.intf2.sock):
            self.intf1.sock.send(pkt)

        return True

class bitw_flowsplitter(yapc.daemon):
    def __init__(self):
        yapc.daemon.__init__(self)
        self.extintf = "eth1"

    def configure_veth(self, intfmgr):
        intfmgr.add_veth()
        intfmgr.set_eth_addr(intfmgr.veth[0].names[1],
                             intfmgr.ethernet_addr(self.extintf))
        intfmgr.up(intfmgr.veth[0].names[0])

    def run(self):
        server = core.core()
        intfmgr=neti.interfacemgr(server)

        self.configure_veth(intfmgr)
        fs = flowsplitter(server, self.extintf,
                          intfmgr.veth[0].names[0])

        server.run()
        sys.exit(0)

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+""
    print "\tBump-in-the-wire (TCP flow splitter)"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-v/--verbose\n\tVerbose output"
    print "--very-verbose\n\tVery verbose output"
    print "-d/--daemon\n\tRun as daemon"

bfs = bitw_flowsplitter()
output.set_mode("INFO")

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvd",
                               ["help","verbose","daemon", 
                                "very-verbose"])
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
    elif (opt in ("-d","--daemon")):
        bfs.daemon=True
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

bfs.start()

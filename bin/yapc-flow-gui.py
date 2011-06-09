#!/usr/bin/env python
import yapc.core as core
import yapc.log.output as output
import yapc.comm.openflow as ofcomm
import yapc.gui.core as gui
import simplejson
import sys
import getopt
from PyQt4 import QtGui, QtCore

class yapc_gui:
    def __init__(self):
        pass

    def run(self):
        ##yapc base
        server = core.core()
        ofconn = ofcomm.ofserver(server)
       
        server.run(runbg=True)
        app=QtGui.QApplication([])
        ret = gui.MainWindow("Flow Manager",500,650).run(app)
        sys.exit(ret)

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" [options]"
    print "\tController with graphical user interface"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-v/--verbose\n\tVerbose output"

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvs:",
                               ["help","verbose","sock="])
except getopt.GetoptError:
    print "Option error!"
    usage()
    sys.exit(2)

output.set_mode("INFO")
ygui = yapc_gui()

#Parse options
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-v","--verbose")):
        output.set_mode("DBG")
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

ygui.run()

#!/usr/bin/env python
import yapc.core as core
import yapc.interface as yapc
import yapc.log.output as output
import yapc.local.networkstate as ns
import yapc.util.terminal as term
import os
import sys
import getopt
import termios, fcntl, sys, os

class bwm(ns.interface_bandwidth):
    cols = "%10s %20s %20s %20s"
    s = ["/","-","\\","|"]
    def __init__(self, server, interval=5, procfile="/proc/net/dev"):
        ns.interface_bandwidth.__init__(self, server, interval, procfile)

        self.mode = "bps"
        self.unit = "K"
        self.clear = True
        self.server = server

        server.register_event_handler(term.keyevent.name, self)

    def processevent(self, event):
        if (isinstance(event, term.keyevent)):
            ##Handle keystokes
            c = event.pop_char()
            while (c != None):
                if (c == "+"):
                    self.interval += 1
                elif (c == "-"):
                    self.interval -= 1
                    if (self.interval < 1):
                        self.interval = 1
                elif (c == "q"):
                    self.server.cleanup()

                c = event.pop_char()
            self.print_screen()

        elif (isinstance(event, yapc.priv_callback)):
            ##Refresh readings
            ns.interface_bandwidth.processevent(self, event)

            try:
                self.i += 1
            except:
                self.i = 0
            if (self.i >= len(bwm.s)):
                self.i = 0

            self.print_screen()

        return True

    def print_screen(self):
        if self.clear:
            os.system("clear")
        vtotal = {}
        vtotal["interface"] = "Total"
        for t in ["transmit", "receive"]:
            vtotal[t] = {} 
            vtotal[t][self.mode] = 0

        print "yapc-bwm.py (probing %s every %.0f seconds)" % (self.procfile, self.interval)
        print
        print bwm.s[self.i]+(bwm.cols % ("iface","Rx","Tx","Total"))[1:]
        print "="*80
        for k,v in self.lastresult.items():
            print bwm.cols % self.get_line(v)
            
            for t in ["transmit", "receive"]:
                try: 
                    vtotal[t][self.mode] += v[t][self.mode]
                except KeyError:
                    pass
        print "="*80
        print bwm.cols % self.get_line(vtotal)

    def get_line(self, v):
        t = []
        t.append(v["interface"])
        try:
            t.append(self.__get_val(v["receive"][self.mode]))
            t.append(self.__get_val(v["transmit"][self.mode]))
            t.append(self.__get_val(v["receive"][self.mode] + v["transmit"][self.mode]))
        except KeyError:
            t.extend(["N/A", "N/A", "N/A"])
        return tuple(t)

    def __get_val(self, v):
        value = None
        if (self.unit == ""):
            value = v
        elif  (self.unit == "K"):
            value = v/1e3
        elif  (self.unit == "M"):
            value = v/1e6
        elif  (self.unit == "G"):
            value = v/1e9

        if (value == None):
            return "N/A"
        else:
            return "%.2f %s%s" % (value, self.unit, self.mode)

class yapc_bwm(yapc.daemon):
    def __init__(self):
        yapc.daemon.__init__(self)
        self.server = core.core()
        self.bw = bwm(self.server, interval=1)
        self.kl = term.keylogger(self.server)

    def run(self):
        self.server.run()

output.set_mode("INFO")
yb = yapc_bwm()

##Print usage guide
def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" [options]"
    print "\tBandwidth monitor"
    print  "Options:"
    print "-h/--help\n\tPrint this usage guide"
    print "-v/--verbose\n\tVerbose output"
    print "-c/--continuous\n\tDo not clear screen, i.e., print continuously"
    print "-i/--interval\n\tProbe interval"
    for x in ["", "K", "M", "G"]:
        print "-%s/--%sbps\n\tShow in bits per second" % ((x+"b")[0],x)
    print "--very-verbose\n\tVery verbose output"

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvbKMGi:c",
                               ["help","verbose", "very-verbose", "continuous",
                                "bps", "Kbps", "Mbps", "Gbps", "interval="])
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
    elif (opt in ("-b","--bps")):
        yb.bw.unit=""
    elif (opt in ("-K","--Kbps")):
        yb.bw.unit="K"
    elif (opt in ("-M","--Mbps")):
        yb.bw.unit="M"
    elif (opt in ("-G","--Gbps")):
        yb.bw.unit="G"
    elif (opt in ("-i","--interval")):
        yb.bw.interval = int(arg)
    elif (opt in ("-c","--continuous")):
        yb.bw.clear = False
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

yb.start()

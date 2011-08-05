##Local network state
import yapc.interface as yapc
import yapc.log.output as output
import yapc.coin.information as coininfo
import os
import time

class interface_stat(yapc.component):
    """Class to look at current statistics of interfaces

    @author ykk
    @date Auguest 2011
    """
    def __init__(self, server, interval=5, procfile="/proc/net/dev"):
        """Initialize

        @param server yapc core
        @param interval interval to look
        @param procfile file to look into
        """
        ##Proc file
        self.procfile = procfile
        ##Interval
        self.interval = interval
        ##Reference to yapc core
        self._server = server
        ##Last result
        self.lastresult = None
    
        server.post_event(yapc.priv_callback(self), 0) 

    def processevent(self, event):
        """Process event

        @param event event to process
        @return True
        """
        if (isinstance(event, yapc.priv_callback)):
            output.vdbg(self.get_stat())
            self._server.post_event(yapc.priv_callback(self), self.interval)

        return True

    def get_stat(self):
        """Get current stats
        """
        self.lastresult = {}
        fileRef = open(self.procfile, "r")
        ts = time.time()
        for l in fileRef:
            r = self.parse_line(l, ts)
            if (r != None):
                self.lastresult[r["interface"]] = r
        fileRef.close()
        return self.lastresult

    def parse_line(self, line, timestamp):
        """Parse line in /proc/net/dev

        @param line line to parse
        @param timestamp timestamp for reading
        @return dict of value
        """
        linesplitted = line.split(":")
        if (len(linesplitted) == 1):
            return None

        result = {}
        result["interface"] = linesplitted[0].strip()
        result["timestamp"] = timestamp

        values = linesplitted[1].split()
        result["receive"] = {}
        for k in ["bytes","packets", "errs", "drop", "fifo", "frame", "compressed", "multicast"]:
            result["receive"][k] = int(values.pop(0))
        result["transmit"] = {}
        for k in ["bytes","packets", "errs", "drop", "fifo", "colls", "carrier", "compressed"]:
            result["transmit"][k] = int(values.pop(0))

        return result   

class interface_bandwidth(interface_stat):
    """Class to look at current bandwidth of each interface

    @author ykk
    @date Auguest 2011
    """
    def __init__(self, server, interval=5, procfile="/proc/net/dev"):
        """Initialize

        @param server yapc core
        @param interval interval to look
        @param procfile file to look into
        """
        interface_stat.__init__(self, server, interval, procfile)

    def processevent(self, event):
        """Process event

        @param event event to process
        @return True
        """
        if (isinstance(event, yapc.priv_callback)):
            lastr = self.lastresult
            r = self.get_stat()
            output.vdbg(r)

            if (lastr == None):
                self._server.post_event(yapc.priv_callback(self), self.interval)
                return True

            for k,v in r.items():
                for k2 in ["transmit", "receive"]:
                    try:
                        v[k2]["bps"] = (float(v[k2]["bytes"] - lastr[k][k2]["bytes"])*8.0/
                                        (v["timestamp"]-lastr[k]["timestamp"]))
                        v[k2]["pps"] = (float(v[k2]["packets"] - lastr[k][k2]["packets"])/
                                        (v["timestamp"]-lastr[k]["timestamp"]))
                    except KeyError:
                        output.warn("Interface "+str(k)+" is new or removed",
                                    self.__class__.__name__)

            output.dbg(str(self), self.__class__.__name__)
            self._server.post_event(yapc.priv_callback(self), self.interval)

        return True
    
    def __str__(self):
        """String representation
        """
        s = ""
        s += "===============Bandwidth result===============\n"
        for k, v in self.lastresult.items():
            s += "Interface %s transmitted at %.2f bps and received at %.2f bps\n" % \
                (k, v["transmit"]["bps"], v["receive"]["bps"])
            s += "Interface %s transmitted at %.2f pps and received at %.2f pps\n" % \
                (k, v["transmit"]["pps"], v["receive"]["pps"])
        return s

class coin_bw_info(coininfo.publish):
    """Event to publish bandwidth used

    @author ykk
    @date August 2011
    """
    eventname = "Interface Bandwidth Used Information"
    def __init__(self):
        """Initialize
        """
        self.values = []

    def add(self, intf_name, tx_bps, tx_pps, rx_bps, rx_pps):
        """Add interface reading

        @param intf_name name of interface
        @param tx_bps bits per sec transmitted
        @param tx_pps packets per sec transmitted
        @param rx_bps bits per sec received
        @param rx_pps packets per sec received
        """
        i = {}
        i["interface"] =  intf_name
        i["tx_bps"] = tx_bps
        i["tx_pps"] = tx_pps
        i["rx_bps"] = rx_bps
        i["rx_pps"] = rx_pps
        self.values.append(i)
        
    def get_dict(self):
        return self.values[:]

class coin_intf_bandwidth(interface_bandwidth,coininfo.base):
    """Class to extend interface bandwidth to COIN information base
    
    @author ykk
    @date August 2011
    """
    def __init__(self, server, interval=5, procfile="/proc/net/dev"):
        """Initialize

        @param server yapc core
        @param interval interval to look
        @param procfile file to look into
        """
        interface_bandwidth.__init__(self, server, interval, procfile)
        
    def eventname(self):
        """Provide name for event used to publish data
        
        @return list of event name
        """
        return [coin_bw_info.eventname]

    def processevent(self, event):
        if (isinstance(event, yapc.priv_callback)):
            ##Refresh readings
            interface_bandwidth.processevent(self, event)

            cbi = coin_bw_info()
            for k,v in self.lastresult.items():
                try:
                    cbi.add(k, v["transmit"]["bps"], v["transmit"]["pps"],
                            v["receive"]["bps"],  v["receive"]["pps"])
                except KeyError:
                    pass
            self._server.post_event(cbi)

        return True

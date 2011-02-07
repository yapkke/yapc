#!/usr/bin/env python

import yapc.output as output
import yapc.openflowutil as ofutil
import pcap
import dpkt
import sys

output.set_mode("DBG")

pc = pcap.pcap(sys.argv[1])
for ts,pkt in pc:
    dpktpkt = dpkt.ethernet.Ethernet(pkt)
    output.dbg(str(`dpktpkt`))
    ofdata = dpktpkt["data"]["data"]["data"]
    (ofm, dpktp) = ofutil.get_ofp_match(0, ofdata[18:])
    output.dbg(str(`dpktp`))
    output.dbg("OFP MATCH\n"+ofm.show())

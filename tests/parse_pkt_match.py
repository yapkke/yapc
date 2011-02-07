#!/usr/bin/env python

import yapc.output as output
import yapc.openflowutil as ofutil
import pcap
import dpkt
import sys

output.set_mode("DBG")

pc = pcap.pcap(sys.argv[1])
for ts,ofdata in pc:
    (ofm, dpktp) = ofutil.get_ofp_match(0, ofdata)
    output.dbg(str(`dpktp`))
    output.dbg("OFP MATCH\n"+ofm.show())

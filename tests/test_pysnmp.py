#!/usr/bin/env python
import yapc.core as core
import yapc.interface as yapc
import yapc.comm.snmp as snmp
import yapc.output as output
import time

class print_snmp(yapc.component):
    def __init__(self, server):
        server.register_event_handler(snmp.recv_message.name, self)

    def processevent(self, event):
        output.dbg(str(event.address))
        output.dbg(str(event.community))
        for oid, val in event.oid.items():
            output.dbg(oid.prettyPrint()+" = "+val.prettyPrint())
        return True

server = core.core()
output.set_mode("DBG")
snmpget = snmp.snmp_udp_client(server)
snmps = snmp.snmp_udp_server(server, 5000)
ps = print_snmp(server)
server.run(runbg=True)

m1 = snmp.message(
    {(1,3,6,1,2,1,1,1,0): None,
     (1,3,6,1,2,1,1,3,0): None})
reqMsg = m1.pack_msg(m1.pack_get_pdu())

reqMsg2 = snmp.message(
    {(1,3,6,1,2,1,1,1,0): None}).pack_get_msg()

snmpget.send(reqMsg, ('171.67.74.239', 161))
output.dbg("Sent message 1")
snmpget.send(reqMsg2, ('openflow2.stanford.edu', 161))
output.dbg("Sent message 2")

time.sleep(10)
server.cleanup()

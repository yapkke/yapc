#!/usr/bin/env python
import yapc.core as core
import yapc.interface as yapc
import yapc.comm.snmp as snmpcomm
import yapc.util.snmp as snmp
import yapc.output as output
import time
import sys

class print_snmp(yapc.component):
    def __init__(self, server):
        server.register_event_handler(snmp.get_response.name, self)
        self.count = 0
        self.server = server
        
    def processevent(self, event):
        self.count += 1
        if (event.response != None):
            output.dbg(str(event.response.address))
            output.dbg(str(event.response.community))
            for oid, val in event.response.oid.items():
                output.dbg(oid.prettyPrint()+" = "+val.prettyPrint())
        else:
            output.dbg("Error")

        if(self.count == 2):
            self.server.cleanup()
            
        return True

server = core.core()
output.set_mode("DBG")
snmpget = snmp.reliable_snmp(server)
snmps = snmpcomm.snmp_udp_server(server, 5000)
ps = print_snmp(server)
server.run(runbg=True)

m1 = snmpcomm.message(
    {(1,3,6,1,2,1,1,1,0): None,
     (1,3,6,1,2,1,1,3,0): None})
m2 = snmpcomm.message(
    {(1,3,6,1,2,1,1,1,0): None})

snmpget.send(m1, ('127.0.0.1', 161))
output.dbg("Sent message 1")
snmpget.send(m2, ('localhost', 161))
output.dbg("Sent message 2")


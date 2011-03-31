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
        server.register_event_handler(snmp.response.name, self)
        self.count = 0
        self.server = server
        self.realname = None
        
    def processevent(self, event):
        self.count += 1
        if (event.response != None):
            output.dbg(str(event.response.address))
            output.dbg(str(event.response.community))
            if (not event.response.recv_error):
                for oid, val in event.response.oid.items():
                    output.dbg(oid.prettyPrint()+" = "+val.prettyPrint())

                    if (event.response.address[0] == '127.0.0.1'):
                        self.realname = event.response.oid[(1,3,6,1,2,1,1,1,0)]
            else:
                output.dbg("SNMP Error : "+event.response.recv_error.prettyPrint())
        else:
            output.dbg("Error")

        if(self.count == 3):
            self.server.cleanup()
            
        return True

server = core.core()
output.set_mode("VVDBG")
snmpget = snmp.reliable_snmp(server)
snmps = snmpcomm.snmp_udp_server(server, 5000)
ps = print_snmp(server)
server.run(runbg=True)

m1 = snmpcomm.message(
    {(1,3,6,1,2,1,1,1,0): None,
     (1,3,6,1,2,1,1,2,0): None})

snmpget.send(m1, ('openflow2.stanford.edu', 161))
output.dbg("Sent message 1")
snmpget.send(m1, ('localhost', 161))
output.dbg("Sent message 2")

while (ps.count < 2):
    time.sleep(0.1)
    
output.dbg(ps.realname)

m2 = snmpcomm.message(
    {(1,3,6,1,2,1,1,1,0): snmpcomm.V2c_PROTO_MOD.OctetString('KK is stupid')})
snmpget.send(m2, ('localhost', 161), get=False)

while (ps.count < 3):
    time.sleep(0.1)


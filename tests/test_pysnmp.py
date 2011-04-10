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
        self.expectedCount = 4
        
    def processevent(self, event):
        self.count += 1
        if (event.response != None):
            #output.dbg(str(event.response.recv_msg))
            #output.dbg(str(event.response.recv_pdu))
            
            if (not event.response.recv_error):
                if (event.action != snmpget.WALK):
                    output.dbg(str(event.response.version), self.__class__.__name__)
                    output.dbg(str(event.response.address), self.__class__.__name__)
                    output.dbg(str(event.response.community), self.__class__.__name__)           
                    for oid, val in event.response.oid.items():
                        output.dbg(str(oid)+" = "+val.prettyPrint(),
                                   self.__class__.__name__)
                else:
                    m = event.next_walk_msg()
                    if (m != None):
                        for oid, val in event.response.oid.items():
                            output.dbg(str(oid)+" = "+val.prettyPrint(),
                                       self.__class__.__name__)
                        self.expectedCount += 1
                        snmpget.send(m, ('localhost', 161), snmpget.WALK)
            else:
                output.dbg("SNMP Error : "+event.response.recv_error.prettyPrint(),
                           self.__class__.__name__)
        else:
            output.dbg("Error", self.__class__.__name__)

        if(self.count == self.expectedCount):
            self.server.cleanup()
            
        return True

server = core.core()
output.set_mode("DBG")
snmpget = snmp.reliable_snmp(server)
snmps = snmpcomm.snmp_udp_server(server, 5000)
ps = print_snmp(server)
server.run(runbg=True)

m1 = snmpcomm.xet_message(
    {(1,3,6,1,2,1,1,1,0): None,
     (1,3,6,1,2,1,1,2,0): None})

snmpget.send(m1, ('openflow2.stanford.edu', 161), snmpget.GET)
output.dbg("Sent message 1")
snmpget.send(m1, ('localhost', 161), snmpget.GET)
output.dbg("Sent message 2")

while (ps.count < 2):
    time.sleep(0.1)
print
print
    
m2 = snmpcomm.xet_message(
    {(1,3,6,1,2,1,1,1,0): snmpcomm.V2c_PROTO_MOD.OctetString('KK is stupid')})
snmpget.send(m2, ('localhost', 161), snmpget.SET)
output.dbg("Sent set message")

while (ps.count < 3):
    time.sleep(0.1)
print
print

m3 = snmpcomm.xet_message(
    {snmpcomm.V2c_PROTO_MOD.ObjectIdentifier((1,3,6)): None})
ps.walking = True
snmpget.send(m3, ('localhost', 161), snmpget.WALK)
output.dbg("Sent walk message")

while (ps.count < ps.expectedCount):
    time.sleep(0.1)


#!/usr/bin/env python
import yapc.core as core
import yapc.interface as yapc
import yapc.output as output
import yapc.comm.snmp as snmp
import time
import commands

class print_snmp(yapc.component):
    def __init__(self, server):
        server.register_event_handler(snmp.message.name, self)

    def processevent(self, event):
        """Process event
        """
        #SNMP Trap message
        if (isinstance(event, snmp.message) and event.isTrap):
            output.dbg(str(event.recv_pdu),
                       self.__class__.__name__)
            output.dbg(str(event.recv_error),
                       self.__class__.__name__)

            output.dbg("",
                       self.__class__.__name__)
            
            output.dbg(str(event.community),
                       self.__class__.__name__)
            output.dbg(str(event.uptime),
                       self.__class__.__name__)
            output.dbg(str(event.agent_addr),
                       self.__class__.__name__)
            output.dbg(str(event.enterprise),
                       self.__class__.__name__)
            output.dbg(str(event.generic_trap),
                       self.__class__.__name__)
            output.dbg(str(event.specific_trap),
                       self.__class__.__name__)
            output.dbg(str(event.oid),
                       self.__class__.__name__)
            
        return True


output.set_mode("DBG")
server = core.core()
snmpcomm = snmp.snmp_udp_server(server, 9000)
client = snmp.snmp_udp_client(server)
ps = print_snmp(server)

server.run(runbg=True)
time.sleep(1)

#Send using netsnmp
commands.getoutput("snmptrap -v 1 -c public 127.0.0.1:9000 1.3.6.1.2.1.2.2.1.1 192.168.5.2 6 666 1233433")

#Send my own trap
tmsg = snmp.trap_message()
tmsg.enterprise = (1,3,6,1,2,1,2,2,1,1)
tmsg.set_agent_ip_addr('192.168.5.2')
tmsg.generic_trap = 6
tmsg.specific_trap = 666
tmsg.set_uptime(1233433)
msg = tmsg.pack_trap_msg()
client.send(msg, ('127.0.0.1',9000))

time.sleep(5)
server.cleanup()




#!/usr/bin/env python
import yapc.comm.udp as ucomm
import yapc.core as core
import yapc.interface as yapc
import yapc.output as output
import socket
import time
import select

class print_udp(yapc.component):
    def __init__(self, server):
        server.register_event_handler(ucomm.message.name, self)

    def processevent(self, event):
        output.info(event.message,
                    self.__class__.__name__)
        output.info(str(event.address),
                    self.__class__.__name__)
        return True

server = core.core()
output.set_mode("DBG")
userver = ucomm.udpserver(server, 10001)
userver = ucomm.udpserver(server, 10002)
pu = print_udp(server)
server.run(runbg=True)

output.dbg("Sending1")
ucomm.send("Testing1", ('127.0.0.1', 10001))
output.dbg("Sending2")
ucomm.send("Testing2", ('127.0.0.1', 10002))
output.dbg("Sending3")
ucomm.send("Testing3", ('127.0.0.1', 10001))

time.sleep(10)
server.cleanup()




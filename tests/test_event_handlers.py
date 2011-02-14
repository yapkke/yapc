#!/usr/bin/env python

import yapc.core as core
import yapc.interface as yapc
import yapc.output as output
class comp(yapc.component):
    def __init__(self, server):
        server.register_event_handler(yapc.priv_callback.name,
                                      self)
    def process_event(event):
       pass 

class a(comp):
    def __init__(self, server):
        comp.__init__(self, server)
class b(comp):
    def __init__(self, server):
        comp.__init__(self, server)
class c(comp):
    def __init__(self, server):
        comp.__init__(self, server)
class d(comp):
    def __init__(self, server):
        comp.__init__(self, server)

server = core.core()
output.set_mode("DBG")

A = a(server)
B = b(server)
C = c(server)
D = d(server)
            
server.print_event_handlers()                  

server.order_handler(yapc.priv_callback.name,
                     B, D)
output.dbg("Ordered b before d: no change expected")
server.print_event_handlers()                  

server.order_handler(yapc.priv_callback.name,
                     D, C)
output.dbg("Ordered d before c: a, b, d, c expected")
server.print_event_handlers()                  

server.order_handler(yapc.priv_callback.name,
                     C, A)
output.dbg("Ordered c before a: c, a, b, d expected")
server.print_event_handlers()                  

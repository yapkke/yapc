#!/usr/bin/env python

import yapc.log.output as output
import yapc.core as core
import yapc.interface as yapc
import yapc.comm.openflow as ofcomm
import yapc.pyopenflow as pyof
import yapc.events.openflow as ofevents
import yapc.forwarding.flows as flows

class tutorial(yapc.component):
    """Our very simple packet-out based tutorial
    """
    def __init__(self, server, ofconn):
        """Initialize

        Register for the OpenFlow packet-in event
        And save a reference to the connections

        @param server reference to yapc core
        @param ofconn reference to ofconnections to send message later
        """
        self.conn = ofconn
        server.register_event_handler(ofevents.pktin.name,
                                      self)

    def processevent(self, event):
        """Process all the events registered for

        Check for packet-in and :
          create packet out with FLOOD action
          send it (oops.. do check the buffer id to see if buffered)

        @param event event to handle
        """
        if (isinstance(event, ofevents.pktin)):
            output.dbg("Receive an OpenFLow packet in :\n"+\
                       event.pktin.show(),
                       self.__class__.__name__)

            flow = flows.exact_entry(event.match)
            flow.set_buffer(event.pktin.buffer_id)
            flow.add_output(pyof.OFPP_FLOOD)
            
            if (event.pktin.buffer_id == flows.UNBUFFERED_ID):
                ##Not buffered
                self.conn.send(event.sock, flow.get_packet_out().pack()+event.pkt)
                output.vdbg("Flood unbuffered packet with match "+\
                                event.match.show().replace('\n',';'))
          
            else:
                ##Buffered packet
                self.conn.send(event.sock,flow.get_packet_out().pack())
                output.vdbg("Flood buffered packet with match "+\
                                event.match.show().replace('\n',';'))

        return True

##Set the output mode to debugging
output.set_mode("DBG")
##Create yapc's core
server = core.core()
##Create ofserver to handle and maintain OpenFlow connections
ofconn = ofcomm.ofserver(server)
##Parser to generate OpenFlow based event beyond ofcomm.message
ofparse = ofevents.parser(server)
##Our simple tutorial-a packet-out based hub
tut = tutorial(server, ofconn.connections)

#Run it!
server.run()


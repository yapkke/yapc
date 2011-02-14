#!/usr/bin/env python

import yapc.output as output
import yapc.core as core
import yapc.interface as yapc
import yapc.ofcomm as ofcomm
import yapc.pyopenflow as pyof
import yapc.events.openflow as ofevents
import yapc.openflowutil as ofutil

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

            oao = pyof.ofp_action_output()
            oao.port = pyof.OFPP_FLOOD

            po = pyof.ofp_packet_out()
            po.header.xid =  ofutil.get_xid()
            po.in_port = event.match.in_port
            po.actions_len = oao.len
            po.actions.append(oao)
            
            if (event.pktin.buffer_id == po.buffer_id):
                ##Not buffered
                self.conn.db[event.sock].send(po.pack()+event.pkt)
                output.vdbg("Flood unbuffered packet with match "+\
                                event.match.show().replace('\n',';'))
          
            else:
                ##Buffered packet
                po.buffer_id = event.pktin.buffer_id
                self.conn.db[event.sock].send(po.pack())
                output.vdbg("Flood buffered packet with match "+\
                                event.match.show().replace('\n',';'))

        return True

##Set the output mode to debugging
output.set_mode("DBG")
##Create yapc's core
server = core.server()
##Create ofserver to handle and maintain OpenFlow connections
ofconn = ofcomm.ofserver(server)
##Parser to generate OpenFlow based event beyond ofcomm.message
ofparse = ofevents.parser(server)
##Our simple tutorial-a packet-out based hub
tut = tutorial(server, ofconn.connections)

#Run it!
server.run()


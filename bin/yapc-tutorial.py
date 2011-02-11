#!/usr/bin/env python

import yapc.output as output
import yapc.core as core
import yapc.interface as yapc
import yapc.ofcomm as ofcomm
import yapc.pyopenflow as pyof
import yapc.events.openflow as ofevents
import yapc.openflowutil as ofutil

class tutorial(yapc.component):
    def __init__(self, server, ofconn):
        self.conn = ofconn
        server.scheduler.registereventhandler(ofevents.pktin.name,
                                              self)

    def processevent(self, event):
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
                self.conn.db[event.sock].send(po.pack()+event.pkt)
                output.vdbg("Flood unbuffered packet with match "+\
                                event.match.show().replace('\n',';'))
          
            else:
                po.buffer_id = event.pktin.buffer_id
                self.conn.db[event.sock].send(po.pack())
                output.vdbg("Flood buffered packet with match "+\
                                event.match.show().replace('\n',';'))

        return True

output.set_mode("DBG")
server = core.server()
ofconn = ofcomm.ofserver(server)
ofparse = ofevents.parser(server)
tut = tutorial(server, ofconn.connections)

server.run()


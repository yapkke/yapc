##Default forwarding actions
#
# Some forwarding ways of handling unhandled packets
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.output as output
import yapc.ofcomm as ofcomm
import yapc.pyopenflow as pyof
import yapc.openflowutil as ofutil
import sys

class dropflow(yapc.component):
    """Class that drop flows

    @author ykk
    @date Feb 2011
    """
    def __init__(self, conn):
        """Initialize
        """
        ##Reference to connections
        self.conn = conn

    def processevent(self, event):
        """Event handler

        @param event event to handle
        """
        if (event.sock not in self.conn.connections.db):
            self.conn.connections.add(event.sock)

        if (isinstance(event, ofcomm.message)):
            if (event.header.type == pyof.OFPT_PACKET_IN):
                self.dropflow(event)

        return True

    def dropflow(self, event):
        """Drop flow

        @param event packet-in event
        """
        #Get flow
        pktin = pyof.ofp_packet_in()
        pkt = pktin.unpack(event.message)
        output.vdbg("Packet in\n"+pktin.show("\t"),
                    self.__class__.__name__)
        (ofm, dpkt) = ofutil.get_ofp_match(pktin.in_port, pkt)
        output.vdbg("Packet has match\n"+ofm.show("\t"),
                    self.__class__.__name__)
        output.vdbg(str(`dpkt`),
                    self.__class__.__name__)

        #Install dropping flow
        fm = pyof.ofp_flow_mod()
        fm.header.xid = ofutil.get_xid()
        fm.match = ofm
        fm.command = pyof.OFPFC_ADD
        fm.idle_timeout = 5
        fm.buffer_id = pktin.buffer_id
        self.conn.connections.db[event.sock].send(fm.pack())

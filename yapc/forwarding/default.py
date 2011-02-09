##Default forwarding actions
#
# Some forwarding ways of handling unhandled packets
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.output as output
import yapc.events.openflow as ofevents
import yapc.pyopenflow as pyof
import yapc.openflowutil as ofutil

class dropflow(yapc.component):
    """Class that drop flows

    @author ykk
    @date Feb 2011
    """
    def __init__(self, server, conn):
        """Initialize

        @param server yapc core
        @param conn reference to connections
        """
        ##Reference to connections
        self.conn = conn

        server.scheduler.registereventhandler(ofevents.pktin.name, self)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        """
        if (event.sock not in self.conn.connections.db):
            self.conn.connections.add(event.sock)

        if (isinstance(event, ofevents.pktin)):
                self.dropflow(event)

        return True

    def dropflow(self, event):
        """Drop flow

        @param event packet-in event
        """
        #Install dropping flow
        fm = pyof.ofp_flow_mod()
        fm.header.xid = ofutil.get_xid()
        fm.match = event.match
        fm.command = pyof.OFPFC_ADD
        fm.idle_timeout = 5
        fm.buffer_id = event.pktin.buffer_id
        self.conn.connections.db[event.sock].send(fm.pack())

        output.vdbg("Dropping flow with match "+\
                        event.match.show().replace('\n',';'))

        #Do not need to check for buffer_id == -1, since we are
        #dropping packets

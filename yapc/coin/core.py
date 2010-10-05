##COIN core
#
# Client-side OpenFlow Interface for Networking
#
# @author ykk
# @date Oct 2010
#
import yapc.interface as yapc
import yapc.ofcomm as ofcomm
import yapc.pyopenflow as pyopenflow

class openflowhandler(yapc.component):
    """Class to handle OpenFlow packets

    @author ykk
    @date Oct 2010
    """
    def __init__(self):
        """Initialize
        """
        ##OpenFlow connections
        self.connections = ofcomm.connections()

    def processevent(self, event):
        """Process OpenFlow messages
        """
        if isinstance(event, ofcomm.message):
            if (event.sock not in self.connections.db):
                self.connections.add(event.sock)

            if (not self.connections.db[event.sock].handshake):
                self.connections.db[event.sock].dohandshake(event)
            elif (event.header.type == pyopenflow.OFPT_ECHO_REQUEST):
                self.connections.db[event.sock].replyecho(event)
            else:
                output.dbg("Receive message "+header.show().strip().replace("\n",";"))
            
        return True



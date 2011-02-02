##COIN OVS
#
# OVS as switch fabric for COIN
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.jsoncomm as jsoncomm

DPCTL="ovs-dpctl"
OFCTL="ovs-ofctl"

class switch(yapc.component):
    """Class to implement switch fabric using OVS

    @author ykk
    @date Feb 2011
    """
    def __init__(self, conn):
        """Initialize switch fabric

        *@param conn reference to connections
        """
        ##Reference to connections
        self.conn = conn
        ##Dictionary of datapath
        self.datapaths = {}

    def add_dp(self, name):
        """Add datapath with name

        @param name name of datapath
        """
        self.datapaths[name] = datapath(name)

    def processevent(self, event):
        """Process messages
        """
        if isinstance(event, jsoncomm.message):
            pass
        
        return True

class datapath:
    """Class to represent and manage datapath
    
    @author ykk
    @date Feb 2011
    """
    def __init__(self, name):
        """Initialize datapath
        
        @param name name of datapath
        """
        ##Name of datapath
        self.name = name

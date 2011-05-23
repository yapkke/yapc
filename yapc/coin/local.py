##COIN local interfaces
#
# Handles interfaces for local user
# @author ykk
# @date Feb 2011
#
import yapc.log.output as output

class loifmgr:
    """Class to manage COIN's local interface
    
    @author ykk
    @date Feb 2011
    """
    def __init__(self, ifmgr):
        """Initialize

        @param ifmgr reference to interface manager
        """
        ##Dictionary of local interfaces (indexed by name)
        self.intfs= {}
        ##Reference to interface manager
        self.ifmgr = ifmgr

    def add(self, name):
        """Add a new local interface
        """       
        self.intfs[name] = loif(self.ifmgr.add_veth())        
        return self.intfs[name]

class loif:
    """Class to implement loif with OVS

    @author ykk
    @date Feb 2011
    """
    def __init__(self, veth):
        """Initialize local interface

        @param ifmgr reference to interface manager
        """
        ##Name of client facing interface
        self.client_intf = veth.names[1]
        ##Name of switch facing interface
        self.switch_intf = veth.names[0]
        ##Name of interfaces in NAT
        self.interfaces = []
        
    def add_if(self, intf):
        """Add interface to NAT
        """
        self.interfaces.append(intf)
        

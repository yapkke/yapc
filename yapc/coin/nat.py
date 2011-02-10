##COIN NAT mode
#
# Handles interfaces in NAT
# @author ykk
# @date Feb 2011
#
import yapc.output as output

class natmgr:
    """Class to manage COIN's NAT module
    
    @author ykk
    @date Feb 2011
    """
    def __init__(self, ifmgr):
        """Initialize

        @param ifmgr reference to interface manager
        """
        ##Dictionary of NAT (indexed by name)
        self.nats = {}
        ##Reference to interface manager
        self.ifmgr = ifmgr

    def add(self, name):
        """Add a new NAT
        """       
        self.nats[name] = nat(self.ifmgr.add_veth())        
        return self.nats[name]

class nat:
    """Class to implement NAT over ports in OVS

    @author ykk
    @date Feb 2011
    """
    def __init__(self, veth):
        """Initialize NAT

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
        

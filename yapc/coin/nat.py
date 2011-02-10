##COIN NAT mode
#
# Handles interfaces in NAT
#
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

class nat:
    """Class to implement NAT over ports in OVS

    @author ykk
    @date Feb 2011
    """
    def __init__(self, ifmgr):
        """Initialize NAT

        @param ifmgr reference to interface manager
        """
        ##Dictionary of interfaces [port no] = (mac addr, ip addr)
        self.interfaces = {}

class nat_intf:
    """Class to create and manage a NAT interface

    @author ykk
    @date Feb 2011
    """
    def __init__(self, veth_pair):
        """Initialize a NAT interface
        """
        ##Reference to veth pair
        self.veth_pair = veth_pair

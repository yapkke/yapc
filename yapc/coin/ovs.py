##COIN OVS
#
# OVS as switch fabric for COIN
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.jsoncomm as jsoncomm
import yapc.ofcomm as ofcomm
import yapc.output as output
import yapc.commands as cmd

DPCTL="ovs-dpctl"
OFCTL="ovs-ofctl"
CONNECT="ovs-openflowd"

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

    def add_if(self, intf):
        """Add interface to datapath

        @param intf name of interface
        @return command's exit status
        """
        return cmd.run_cmd(DPCTL+" add-if "+self.name+" "+name,
                           self.__class__.__name__)

    def del_if(self, intf):
        """Remove interface to datapath

        @param intf name of interface
        @return command's exit status
        """
        return cmd.run_cmd(DPCTL+" del-if "+self.name+" "+name,
                           self.__class__.__name__)

    def connect(self, controller, port=6633):
        """Connect datapath to controller
        
        @param controller controller's IP address
        @param port port number
        """
        return cmd.run_cmd_screen("coin-ovs ", 
                                  CONNECT+" tcp:"+controller+":"+port,
                                  self.__class__.__name__)

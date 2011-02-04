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
import simplejson

DPCTL="ovs-dpctl"
OFCTL="ovs-ofctl"
CONNECT="ovs-openflowd"

class switch(yapc.component, yapc.cleanup):
    """Class to implement switch fabric using OVS

    @author ykk
    @date Feb 2011
    """
    def __init__(self, conn):
        """Initialize switch fabric

        @param conn reference to connections
        """
        ##Reference to connections
        self.conn = conn
        ##Dictionary of datapath
        self.datapaths = {}

    def __del__(self):
        """Clean up all datapath
        """
        output.dbg("Cleaning up datapaths",
                   self.__class__.__name__)
        for name,dp in self.datapaths.items():
            self.del_dp(name)

    def cleanup(self):
        """Clean up all datapath
        """
        self.__del__()

    def add_dp(self, name):
        """Add datapath with name

        @param name name of datapath
        """
        output.dbg("Add datapath "+name,
                   self.__class__.__name__)
        self.datapaths[name] = datapath(name)

    def del_dp(self, name):
        """Delete datapath with name

        @param name name of datapath
        """
        if (name in self.datapaths):
            output.dbg("Delete datapath "+name,
                       self.__class__.__name__)
            self.datapaths.pop(name)
        else:
            output.err("No datapath of name "+name)

    def processevent(self, event):
        """Process messages

        @param event event to process
        """
        if isinstance(event, jsoncomm.message):
            self.__process_json(event)
        elif isinstance(event, ofcomm.message):
            pass
        
        return True

    def __process_json(self, event):
        """Process JSON messages

        @param event JSON message event to process
        """
        if (event.sock not in self.conn.jsonconnections.db):
            self.conn.jsonconnections.add(event.sock)
        
        if (event.message["type"] == "coin" and
            event.message["subtype"] == "ovs"):
            reply = self.__process_switch_json(event)
            if (reply != None):
                self.conn.jsonconnections.db[event.sock].send(reply)
        else:
            output.dbg("Receive JSON message "+simplejson.dumps(event.message),
                       self.__class__.__name__)

    def __process_switch_json(self, event):
        """Process JSON messages for switch

        @param event JSON message event for switch
        """
        reply = {}
        reply["type"] = "coin"
        reply["subtype"] = "ovs"

        if (event.message["command"] == "add_dp"):
            self.add_dp(event.message["name"])
            reply["executed"] = True
        elif (event.message["command"] == "del_dp"):
            self.del_dp(event.message["name"])
            reply["executed"] = True
        else:
            reply["error"] = "Unknown command"

        return reply

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
        cmd.run_cmd(DPCTL+" add-dp "+name,
                    self.__class__.__name__)
        ##List of interfaces
        self.interfaces = []
        ##Connected to controller or not
        self.connected = False

    def __del__(self):
        """Clean up datapath
        """
        output.dbg("Clean up datapath "+self.name,
                   self.__class__.__name__)
        if (self.connected):
            self.disconnect()
        for i in self.interfaces:
            self.del_if(i)
        cmd.run_cmd(DPCTL+" del-dp "+self.name,
                    self.__class__.__name__)
        
    def add_if(self, intf):
        """Add interface to datapath

        @param intf name of interface
        @return command's exit status
        """
        self.interfaces.append(intf)
        return cmd.run_cmd(DPCTL+" add-if "+self.name+" "+name,
                           self.__class__.__name__)

    def del_if(self, intf):
        """Remove interface to datapath

        @param intf name of interface
        @return command's exit status
        """
        self.interfaces.remove(intf)
        return cmd.run_cmd(DPCTL+" del-if "+self.name+" "+name,
                           self.__class__.__name__)

    def connect(self, controller, port=6633):
        """Connect datapath to controller
        
        @param controller controller's IP address
        @param port port number
        """
        self.connected = True
        return cmd.run_cmd_screen("coin-ovs-"+self.name, 
                                  CONNECT+" tcp:"+controller+":"+port,
                                  self.__class__.__name__)

    def disconnect(self):
        """Disconnect datapath from controller
        """
        self.connected = False
        return cmd.run_cmd("screen -d -r coin-ovs-"+self.name+\
                               " -X quit")
    

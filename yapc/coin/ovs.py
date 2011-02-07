##COIN OVS
#
# OVS as switch fabric for COIN
#
# @author ykk
# @date Feb 2011
#
import yapc.local.ovs as ovs
import yapc.interface as yapc
import yapc.jsoncomm as jsoncomm
import yapc.output as output
import yapc.netstate.switches as swstate
import yapc.memcacheutil as mc
import simplejson
import string

COIN_DP_NAME = "dp0"

class switch(yapc.component, ovs.switch):
    """Class to implement switch fabric using OVS

    @author ykk
    @date Feb 2011
    """
    def __init__(self, server, conn, host='127.0.0.1', port=6633):
        """Initialize switch fabric

        @param server yapc core
        @param conn reference to connections
        @param host host to connect to
        @param port port number to connect to
        """
        ovs.switch.__init__(self)
        ##Reference to connections
        self.conn = conn
        #Add datapath and connect
        self.add_dp(COIN_DP_NAME)
        self.datapaths[COIN_DP_NAME].connect(host,port)

        mc.get_client()

        server.scheduler.registereventhandler(jsoncomm.message.name, self)
        server.scheduler.registercleanup(self)

    def processevent(self, event):
        """Process messages

        @param event event to process
        """
        if isinstance(event, jsoncomm.message):
            self.__process_json(event)
        
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

        if (event.message["command"] == "add_if"):
            self.datapaths[COIN_DP_NAME].add_if(event.message["name"])
            reply["executed"] = True
        elif (event.message["command"] == "del_if"):
            self.datapaths[COIN_DP_NAME].del_if(event.message["name"])
            reply["executed"] = True
        elif (event.message["command"] == "get_interfaces"):
            dpidsl = mc.get(swstate.dp_features.DP_SOCK_LIST)
            if (dpidsl != None):
                reply["interfaces"] = []
                if (len(dpidsl) > 0):
                    output.warn(str(len(dpidsl))+" datapaths connected to COIN",
                                self.__class__.__name__)
                f = mc.get(dpidsl[0])
                output.dbg("Updated switch features:\n"+\
                               f.show("\t"),
                           self.__class__.__name__)
                for p in f.ports:
                    reply["interfaces"].append(filter(lambda x: 
                                                      x in string.printable, 
                                                      p.name))
            else:
                output.warn("No datapaths connected to COIN",
                            self.__class__.__name__)
                reply["error"] = "No datapath connected"
        else:
            reply["error"] = "Unknown command"

        return reply

    

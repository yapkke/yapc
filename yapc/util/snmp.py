import yapc.comm.snmp as snmpcomm
import yapc.interface as yapc
import yapc.output as output

class response(yapc.event):
    """Class of reliable SNMP GET and RESPONSE

    @author ykk
    @date Mar 2011
    """
    name = "SNMP Response"
    def __init__(self, entry, recv_msg=None):
        """Initialize with get and response
        """
        ##SNMP recv_message is successful, else None
        self.response = recv_msg
        ##What is tried
        self.request = entry["request"]
        self.timeout = entry["timeout"]
        self.retry = entry["retry"]
        self.tried = entry["tried"]
        self.addr = entry["addr"]

    def next_walk_obj(self):
        """Get object for snmp walk

        @return object (oid, val) else None
        """
        varTab =  snmpcomm.V2c_PROTO_MOD.apiPDU.getVarBindTable(self.request.pack_walk_pdu(),
                                                                self.response.recv_pdu)
        for oid, val in varTab[-1]:
            if (val == None):
                return None
            else:
                return oid
     
class reliable_snmp(yapc.component):
    """Class to implement reliable SNMP GET

    @author ykk
    @date Mar 2011
    """
    GET = 1
    SET = 2
    WALK = 3
    def __init__(self, server, client=None):
        """Initialize

        @param server yapc core
        """
        ##Reference to server
        self.server = server
        ##Dictionary of dictionary of request and retries indexed by request id
        self.messages = {}
        ##Reference to UDP client
        self.client = client
        if (self.client == None):
            self.client = snmpcomm.snmp_udp_client(server)

        server.register_event_handler(snmpcomm.recv_message.name, self)

    def processevent(self, event):
        """Process events
        which includes
        * SNMP received message
        * Private callback for timeout

        @param event events to process
        """
        if (isinstance(event, snmpcomm.recv_message)):
            ##Got response
            rspId = event.get_req_id(event.recv_pdu)
            self.server.post_event(response(self.messages[rspId],
                                                event))
            del self.messages[rspId]
            
        elif (isinstance(event, yapc.priv_callback)):
            ##Timeout and retry
            if (event.magic in self.messages):
                if ((self.messages[event.magic]["tried"] <
                    self.messages[event.magic]["retry"]) or
                    self.messages[event.magic]["retry"] == None):

                    self.send(self.messages[event.magic]["request"],
                              self.messages[event.magic]["addr"],
                              self.messages[event.magic]["action"],
                              self.messages[event.magic]["timeout"],
                              self.messages[event.magic]["retry"],
                              self.messages[event.magic]["tried"])
                    del self.messages[event.magic]
                else:
                    self.server.post_event(response(self.messages[event.magic]))
                    output.dbg("Giving up on SNMP GET with id "+str(event.magic)+\
                               " after trying for "+\
                               str(self.messages[event.magic]["tried"])+ " times",
                               self.__class__.__name__)
                    del self.messages[event.magic]
                    
        return True
            
    def send(self, message, addr, action, timeout=3, retry=10, tried=0):
        """Send snmp.message

        @param message SNMP message to send
        @param addr (host, port) to send to
        @param timeout timeout in how many seconds
        @param retry number of times to retry (if None, try indefinitely)
        """
        pdu=None
        if (action == self.GET):
            pdu = message.pack_get_pdu()
        elif (action == self.SET):
            pdu = message.pack_set_pdu()
        elif (action == self.WALK):
            pdu = message.pack_walk_pdu()
            
        msg = message.pack_msg(pdu)
        reqId = message.get_req_id(pdu)
        output.dbg("Transmitting SNMP message with id "+str(reqId)+\
                   " for the no. "+str(tried+1)+ " time",
                   self.__class__.__name__)
        self.client.send(msg, addr)
        self.messages[reqId] = {"timeout": timeout,
                                "retry": retry,
                                "tried": tried+1,
                                "request": message,
                                "addr": addr,
                                "action": action}
        self.server.post_event(yapc.priv_callback(self, reqId), timeout)

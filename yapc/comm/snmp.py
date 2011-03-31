from pysnmp.proto import api
from pyasn1.codec.ber import encoder, decoder
import yapc.comm.udp as ucomm
import yapc.output as output

V2c_PROTO_MOD = api.protoModules[api.protoVersion2c]

class message:
    """Class to represent SNMP message

    @author ykk
    @date Mar 2011
    """
    def __init__(self, oid=None, community="public"):
        """Initialize

        @param oid dictionary of oid
        @param community community string
        """
        ##Community string
        self.community = community
        ##List of oid
        self.oid = oid
        if (self.oid == None):
            self.oid = {}

    def get_req_id(self, pdu, pMod=V2c_PROTO_MOD):
        """Get request id of PDU
        """
        return pMod.apiPDU.getRequestID(pdu)

    def unpack_msg(self, msg, pMod=V2c_PROTO_MOD):
        """Unpack a SNMP message
        """
        snmp_msg, m = decoder.decode(msg,
                                     asn1Spec=pMod.Message())
        snmp_pdu = pMod.apiMessage.getPDU(snmp_msg)
        snmp_error = pMod.apiPDU.getErrorStatus(snmp_pdu)

        self.community = pMod.apiMessage.getCommunity(snmp_msg)
        self.oid = {}
        if (not snmp_error):
            for oid, val in pMod.apiPDU.getVarBinds(snmp_pdu):
                self.oid[oid] = val
                
        return (snmp_msg, snmp_pdu, snmp_error)

    def pack_get_pdu(self, pMod=V2c_PROTO_MOD):
        """Pack and return request PDU
        """
        reqPDU = pMod.GetRequestPDU()
        pMod.apiPDU.setDefaults(reqPDU)
        x = []
        for o,v in self.oid.items():
            if (v == None):
                x.append((o, pMod.Null()))
            else:
                x.append((o, v))
        pMod.apiPDU.setVarBinds(reqPDU,tuple(x))

        return reqPDU

    def pack_get_msg(self, pMod=V2c_PROTO_MOD):
        """Shortcut to pack GET message
        """
        return self.pack_msg(self.pack_get_pdu(pMod), pMod)

    def pack_msg(self, pdu, pMod=V2c_PROTO_MOD):
        """Pack and return request message
        """
        msg = pMod.Message()
        pMod.apiMessage.setDefaults(msg)
        pMod.apiMessage.setCommunity(msg, self.community)
        pMod.apiMessage.setPDU(msg, pdu)
        return msg

class recv_message(message, ucomm.message):
    """SNMP message received

    @author ykk
    @date Mar 2011
    """
    name = "SNMP Received Message"
    def __init__(self, sock, msg, addr):
        """Initialize with message
        """
        message.__init__(self)
        ucomm.message.__init__(self, sock, msg, addr)
        self.recv_msg, self.recv_pdu, self.recv_error = \
                       self.unpack_msg(self.message)

    def reply(self, msg):
        """Reply with message
        """
        ucomm.message.reply(self, encoder.encode(msg))

class snmp_udp_server(ucomm.udpserver):
    """Class for SNMP UDP server connection

    @author ykk
    @date Mar 2011
    """
    def __init__(self, server, port, host='', snmpservermgr=None):
        """Initialize
        """
        self.snmpservermgr = snmpservermgr
        if (self.snmpservermgr == None):
            self.snmpservermgr = snmpsocket(server)
        ucomm.udpserver.__init__(self, server, port, host, self.snmpservermgr)

class snmp_udp_client(ucomm.udpclient):
    """Class for SNMP UDP client connection

    @author ykk
    @date Mar 2011
    """
    def __init__(self, server, snmpclientmgr=None):
        """Initialize
        """
        self.snmpclientmgr = snmpclientmgr
        if (self.snmpclientmgr == None):
            self.snmpclientmgr = snmpsocket(server)
        ucomm.udpclient.__init__(self, server, self.snmpclientmgr)
        
    def send(self, msg, addr):
        """Send SNMP message

        @param msg pysnmp's message
        @param addr (host, ip)
        """
        ucomm.udpclient.send(self, encoder.encode(msg), addr)

class snmpsocket(ucomm.udpsocket):
    """Class to receive SNMP UDP packets from socket

    @author ykk
    @date Mar 2011
    """
    def __init__(self, scheduler=None, maxlen=2048):
        """Initialize
        """
        ucomm.udpsocket.__init__(self, scheduler, maxlen)

    def receive(self, sock, recvthread):
        """Receive new message
        """
        output.vvdbg("Receiving SNMP packet on UDP socket "+str(sock),
                    self.__class__.__name__)        
        data, addr = sock.recvfrom(self.maxlen)
        self.scheduler.post_event(recv_message(sock, data, addr))

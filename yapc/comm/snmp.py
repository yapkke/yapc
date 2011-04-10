from pysnmp.proto import api
from pyasn1.codec.ber import encoder, decoder
from pyasn1.type import univ
import yapc.interface as yapc
import yapc.comm.udp as ucomm
import yapc.output as output
import socket
import time

V2c_PROTO_MOD = api.protoModules[api.protoVersion2c]

class base_message:
    """Class to represent basic SNMP message

    @author ykk
    @date Apr 2011
    """
    def __init__(self, oid=None, community="public", isTrap=False):
        """Initialize

        @param community community string
        """
        #Version
        self.version = api.protoVersion2c
        #Community string
        self.community = community
        #List of oid
        self.oid = oid
        if (self.oid == None):
            self.oid = {}
        #Message is trap or not
        self.isTrap = isTrap

    def unpack_msg(self, msg):
        """Unpack a SNMP message
        """
        self.version = api.decodeMessageVersion(msg)
        pMod = api.protoModules[int(self.version)]

        snmp_msg, m = decoder.decode(msg,
                                     asn1Spec=pMod.Message())
        snmp_pdu = pMod.apiMessage.getPDU(snmp_msg)
        snmp_error = pMod.apiPDU.getErrorStatus(snmp_pdu)

        self.community = pMod.apiMessage.getCommunity(snmp_msg)
        self.isTrap = snmp_pdu.isSameTypeWith(pMod.TrapPDU())

        return (snmp_msg, snmp_pdu, snmp_error)

    def set_oid_val(self, oid, value):
        """Set oid to value

        @param oid oid string (not encoded)
        @param value object holding value (encoded)
        """
        self.oid[oid] = value

    def encode_oid(oid):
        return univ.ObjectIdentifier(oid)
    encode_oid = yapc.static_callable(encode_oid)

    def encode_int(int):
        return univ.Integer(int)
    encode_int = yapc.static_callable(encode_int)

    def encode_string(string):
        return univ.OctetString(string)
    encode_string = yapc.static_callable(encode_string)

class trap_message(base_message):
    """Class to represent SNMP trap message

    @author ykk
    @date Apr 2011
    """
    def __init__(self, oid=None, community="public"):
        """Initialize

        @param community community string
        """
        base_message.__init__(self, oid, community, True)
        #Uptime
        self.uptime = None
        #Enterprise
        self.enterprise = None
        #Agent address
        self.agent_addr = socket.gethostbyname(socket.gethostname())
        #Generic trap
        self.generic_trap = None
        #Specific trap
        self.specific_trap = None

    def pack_trap_msg(self):
        pass

    def unpack_trap_pdu(self, snmp_pdu):
        """Unpack a SNMP Trap message
        """
        pMod = api.protoModules[int(self.version)]
        #Decode trap
        if (self.version == api.protoVersion1):
            self.enterprise = pMod.apiTrapPDU.getEnterprise(snmp_pdu)
            self.agent_addr = pMod.apiTrapPDU.getAgentAddr(snmp_pdu)
            self.generic_trap = pMod.apiTrapPDU.getGenericTrap(snmp_pdu)
            self.specific_trap = pMod.apiTrapPDU.getSpecificTrap(snmp_pdu)
            self.uptime = pMod.apiTrapPDU.getTimeStamp(snmp_pdu)    
            varBinds = pMod.apiTrapPDU.getVarBindList(snmp_pdu)
        else:
            varBinds = pMod.apiPDU.getVarBindList(snmp_pdu)
        for oid, val in varBinds:
            self.oid[oid._value] = val
            
class xet_message(base_message):
    """Class to represent SNMP GET/SET message

    @author ykk
    @date Mar 2011
    """
    def __init__(self, oid=None, community="public"):
        """Initialize

        @param oid dictionary of oid
        @param community community string
        """
        base_message.__init__(self, oid, community)

    def get_req_id(self, pdu, pMod=V2c_PROTO_MOD):
        """Get request id of PDU
        """
        return pMod.apiPDU.getRequestID(pdu)

    def unpack_xet_pdu(self, snmp_pdu):
        """Unpack a SNMP GET/SET PDU
        """
        pMod = api.protoModules[int(self.version)]
        self.oid = {}
        for oid, val in pMod.apiPDU.getVarBinds(snmp_pdu):
            self.oid[oid._value] = val

    def __pack_pdu(self, reqPDU, pMod=V2c_PROTO_MOD):
        """Pack generic get/set PDU
        """
        pMod.apiPDU.setDefaults(reqPDU)
        x = []
        y = []
        for o,v in self.oid.items():
            if (isinstance(o, pMod.ObjectIdentifier)):
                ##Set oid for GETNEXT (walk)
                y.append(o)
            else:
                 ##Set oid, val for GET/SET
                if (v == None):
                    x.append((o, pMod.Null()))
                else:
                    x.append((o, v))

        if (len(x) != 0):
            pMod.apiPDU.setVarBinds(reqPDU,tuple(x))
        else:
            pMod.apiPDU.setVarBinds(reqPDU,
                                    map(lambda x, pMod=pMod: (x, pMod.Null()), y))

        return reqPDU

    def pack_walk_pdu(self, pMod=V2c_PROTO_MOD):
        """Pack and return GETNEXT (walk) PDU
        """
        return self.__pack_pdu(pMod.GetNextRequestPDU(), pMod)

    def pack_walk_msg(self, pMod=V2c_PROTO_MOD):
        """Shortcut to pack GETNEXT (walk) message
        """
        return self.pack_msg(self.pack_walk_pdu(pMod), pMod)

    def pack_set_pdu(self, pMod=V2c_PROTO_MOD):
        """Pack and return set PDU
        """
        return self.__pack_pdu(pMod.SetRequestPDU(), pMod)

    def pack_set_msg(self, pMod=V2c_PROTO_MOD):
        """Shortcut to pack SET message
        """
        return self.pack_msg(self.pack_set_pdu(pMod), pMod)

    def pack_get_pdu(self, pMod=V2c_PROTO_MOD):
        """Pack and return request PDU
        """
        return self.__pack_pdu(pMod.GetRequestPDU(), pMod)
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

class message(xet_message, trap_message, ucomm.message):
    """SNMP message

    @author ykk
    @date Mar 2011
    """
    name = "SNMP Received Message"
    def __init__(self, sock, msg, addr):
        """Initialize with message
        """
        base_message.__init__(self)
        xet_message.__init__(self)
        trap_message.__init__(self)
        ucomm.message.__init__(self, sock, msg, addr)
        self.recv_msg, self.recv_pdu, self.recv_error = \
                       self.unpack_msg(self.message)

    def unpack_msg(self, msg):
        """Unpack a SNMP message
        """
        (snmp_msg, snmp_pdu, snmp_error) = base_message.unpack_msg(self, msg)
        if (self.isTrap):
            self.unpack_trap_pdu(snmp_pdu)
        else:
            if (not snmp_error):
                self.unpack_xet_pdu(snmp_pdu)
            
        return (snmp_msg, snmp_pdu, snmp_error)

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
        self.scheduler.post_event(message(sock, data, addr))
       

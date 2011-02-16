# $Id: lldp.py 2011-02-15 21:47:00P ykk $

"""Link Layer Discovery Protocol."""

import dpkt
import struct

# LLDP ethertype
LLDP_ETH = 0x88cc

LLDP_END_TYPELEN = 0

LLDP_TYPE_MASK = 0xfe00
LLDP_LENGTH_LEN = 9
LLDP_LENGTH_MASK = 0x01ff

class LLDP_TLV(dpkt.Packet):
    __hdr__ = (
        ('typelen', 'H', 0),
        )
    
    def unpack(self, buf):
        dpkt.Packet.unpack(self, buf)
        self.type = (self.typelen & LLDP_TYPE_MASK) >> LLDP_LENGTH_LEN
        self.len = self.typelen & LLDP_LENGTH_MASK
        if (self.typelen == LLDP_END_TYPELEN):
            self.data = ""
        else:
            self.value = buf[2:self.len+2]
            self.data = LLDP_TLV(buf[self.len+2:])
            
    def __str__(self):
        if (self.type != LLDP_END_TYPELEN):
            self.len = len(self.value)
        else:
            self.len = 0
        self.typelen = (self.type << LLDP_LENGTH_LEN) | self.len
        if (self.type != LLDP_END_TYPELEN):
            return self.pack_hdr() + self.value + str(self.data)
        else:
            return self.pack_hdr()

class LLDP(LLDP_TLV):
    pass

if __name__ == '__main__':
    import unittest
    
    class LLDPTestCase(unittest.TestCase):
        def test_lldp(self):
            s = '\x02\x11\x07'+"deadbeefcafecafe"\
                '\x04\x05\x07'+"0008"\
                '\x06\x02\x00\x3c'\
                '\x00\x00'
            lldp = LLDP(s)
            if (s != lldp.pack()):
                raise dpkt.PackError

    unittest.main()

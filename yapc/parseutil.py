##Parsing utilities
#
# @author ykk
# @date Oct 2010
#
import yapc.output as output
import struct

def get_null_terminated_str(s):
    """Get null terminated string

    @param s referenence to string
    """
    output.dbg(str(struct.unpack("B"*len(s), s)),
               "parse utility")
    return s[:s.find('\x00')]

def is_multicast_mac(mac_array):
    """Determine if mac is multicast
    """
    return ((mac_array[0] % 2) == 1)

def byte_str2array(str):
    """Convert binary str to array

    @param str binary string
    @return array of values
    """
    r = []
    for i in range(0, len(str)):
        r.append(struct.unpack("B", str[i])[0])
    return r

def array2val(array):
    """Convert array to value

    @param array
    @return value
    """
    r = 0
    a = array[:]
    a.reverse()
    for i in range(0, len(a)):
        r += a[i] * pow(2,8*i)
    return r

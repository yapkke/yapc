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

class ipv4addr:
    """Class that parse IPv4 address
    """
    def __init__(self, ip):
        """Initialize
        with string xxx.xxx.xxx.xxx
        """
        self.ipvalues = None
        if isinstance(ip, str) and (ip.find(".") != 0):
            iptuple = ip.split(".")
            self.ipvalues = []
            for ipval in iptuple:
                self.ipvalues.append(int(ipval))

        #Checkout validity
        if not self.__check():
            self.ipvalues = None

    def value(self):
        """Return value in integer
        """
        if (self.ipvalues == None):
            return None
        
        val = 0
        i = 0
        for ipval in self.ipvalues:
            val += ipval*pow(2,i)
            i += 8
        return val

    def __check(self):
        """Check validity of IP address
        """
        #Check length
        if (len(self.ipvalues) != 4):
            return False
        
        #Check value
        for ipval in self.ipvalues:
            if (ipval < 0) or (ipval > 255):
                return False

        #Check first value is non-zero
        if (self.ipvalues[0] == 0):
            return False
        
        return True

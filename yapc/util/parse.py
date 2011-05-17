##Parsing utilities
#
# @author ykk
# @date Oct 2010
#
import yapc.log.output as output
import struct
import socket
import os

global oui_file
oui_file = None

def __get_oui_file(filename=None):
    global oui_file
    if (oui_file != None):
        return

    if (filename==None):
        filename = __file__
        filename = filename[:filename.rfind("/")]
        filename +="/oui.txt"

    oui_file= {}
    fileRef = open(filename, "r")
    lastline = ""
    for l in fileRef:
        sl = l.strip()
        if (sl != "" and
            lastline == ""):
            r = sl.split("(hex)")
            if (len(r) >= 2):
                oui_file[r[0].strip()] = r[1].strip()
        lastline = sl
    fileRef.close()

def get_null_terminated_str(s):
    """Get null terminated string

    @param s referenence to string
    """
    output.dbg(str(struct.unpack("B"*len(s), s)),
               "parse utility")
    return s[:s.find('\x00')]

def ip_val2binary(value):
    """Get packed IP string given value

    @param value value of IP address (long)
    """
    return struct.pack(">L", value)

def ip_binary2val(packed):
    """Get value of IP from packed string
    """
    return struct.unpack(">L", packed)[0]

def ip_val2string(value):
    """Get IP string given value

    @param value value of IP address (long)
    """
    return socket.inet_ntoa(ip_val2binary(value))

def ip_string2val(string):
    """Get value of IP address from string
    """
    return ip_binary2val(ip_string2binary(string))

def ip_string2binary(string):
    """Get packed IP string from string
    """
    return socket.inet_aton(string)

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

def array2byte_str(array):
    """Convert array to binary str
    
    @param array array of value
    @return binary string
    """
    r = ""
    for i in range(0, len(array)):
        r += struct.pack("B", array[i])
    return r

def array2hex_str(array,separator=":",minlen=2):
    r = ""
    for i in range(0, len(array)):
        r += ("%0"+str(minlen)+"x") % array[i]+separator
    return r[:-1]

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

def get_oui(array):
    if (len(array) < 3):
        return None
    
    return array2hex_str(array, "-")[:8] 

def get_oui_name(oui):
    if (len(oui) != 8):
        return

    __get_oui_file()
    try:
        return oui_file[oui.replace(":","-").upper()]
    except KeyError:
        return None
    

##Memcache library
#
# Some default parameters for memcache in yapc
#
# @author ykk
# @date Feb 2011
#
import memcache
import time
import yapc.output as output

##Global memcache client
global memcache_client
memcache_client = None

##Servers address
global memcache_servers
memcache_servers = ['127.0.0.1:11211']

##On/Off switch
global memcache_mode
MEMCACHE_MODE = {"ON":0,
                 "OFF" = 1,
                 "LOCAL" = 2}
memcache_mode = MEMCACHE_MODE["ON"]

##Memcache debug
DEBUG = 1

def get_client():
    """Get client for memcache

    @param servers list of servers
    @param debug debug mode
    """
    global memcache_client
    global memcache_servers
    global memcache_mode
    if (memcache_mode == MEMCACHE_MODE["OFF"]):
        return 
 
    if (memcache_client== None):
        if (memcache_mode == MEMCACHE_MODE["ON"]):
            memcache_client = memcache.Client(memcache_servers,
                                              DEBUG)
            memcache_client.flush_all()
        elif (memcache_mode == MEMCACHE_MODE["LOCAL"]):
            memcache_client = local_memcache()
    return memcache_client

def set(name, value, timeout=0):
    """Set key and value

    @param name key name
    @param value value to set key to
    @param timeout timeout to expire data
    """
    global memcache_on
    if (not memcache_on):
        return None

    if (name.find(" ") != -1):
        output.warn("Memcache key cannot contain spaces",
                    "memcache util")
    return memcache_client.set(name, value, timeout)

def get(name):
    """Get value of key
    
    @param name key name
    @return value
    """
    global memcache_on
    if (not memcache_on):
        return None

    return memcache_client.get(name)

def delete(name):
    """Delete key-value

    @param name key name
    """
    global memcache_on
    if (not memcache_on):
        return None

    return memcache_client.delete(name)

def socket_str(sock):
    """Get string for socket
    """
    return str(`sock`).replace(" ","").strip()

class local_memcache:
    """Class that stores key value like memcache locally

    @author ykk
    @date Apr 2011
    """
    def __init__(self):
        """Initialize
        """
        #Dictionary
        self.dict = {}

    def get(self, name):
        """Get value with key
        """
        try:
            (value, timeout) = self.dict[name]
            if ((timeout == 0) or (timeout > time.time())):
                return value
            else:
                self.delete(name)
        except KeyError:
            return None

    def set(self, name, value, timeout):
        """Set value with key
        """
        if (timeout == 0):
            self.dict[name] = (value, timeout)
        else:
            self.dict[name] = (value, time.time()+timeout)

    def delete(self, name):
        """Delete key
        """
        del self.dict[name]

##Memcache library
#
# Some default parameters for memcache in yapc
#
# @author ykk
# @date Feb 2011
#
import memcache
import yapc.output as output

##Global memcache client
global memcache_client
memcache_client = None

##Servers address
global memcache_servers
memcache_servers = ['127.0.0.1:11211']

##On/Off switch
global memcache_on
memcache_on = True

##Memcache debug
DEBUG = 1

def get_client():
    """Get client for memcache

    @param servers list of servers
    @param debug debug mode
    """
    global memcache_client
    global memcache_servers
    global memcache_on
    if (not memcache_on):
        return 

    if (memcache_client== None):
        memcache_client = memcache.Client(memcache_servers,
                                          DEBUG)
        memcache_client.flush_all()
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

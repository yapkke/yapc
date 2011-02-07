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

##Server address
MEMCACHE_SERVER = ['127.0.0.1:11211']

def get_client(servers=MEMCACHE_SERVER, debug=1):
    """Get client for memcache

    @param servers list of servers
    @param debug debug mode
    """
    global memcache_client
    if (memcache_client== None):
        memcache_client = memcache.Client(servers, debug)
    return memcache_client

def set(name, value):
    """Set key and value

    @param name key name
    @param value value to set key to
    """
    if (name.find(" ") != -1):
        output.warn("Memcache key cannot contain spaces",
                    "memcache util")
    return memcache_client.set(name, value)

def get(name):
    """Get value of key
    
    @param name key name
    @return value
    """
    return memcache_client.get(name)

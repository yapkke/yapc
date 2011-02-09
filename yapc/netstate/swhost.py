##Host state that pertain to individual switch
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.memcacheutil as mc
import yapc.parseutil as pu
import yapc.events.openflow as ofevents
import yapc.output as output
import time

class mac2sw_binding(yapc.component):
    """Class learns which port of the switch is the mac address binded to

    @author ykk
    @date Feb 2011
    """
    ##Key prefix for binding records
    MAC2SW_BINDING_PREFIX ="mac2sw_binding_"
    ##Timeout
    TIMEOUT = 60
    def __init__(self, server):
        """Initialize

        @param server yapc core
        """
        mc.get_client()
        server.scheduler.registereventhandler(ofevents.pktin.name, self)

    def get_key(sock, mac):
        """Get key to retrieve binding between switch and mac
        """
        return mac2sw_binding.MAC2SW_BINDING_PREFIX +\
            mc.socket_str(sock) +\
            "%x" % pu.array2val(mac)
    get_key = yapc.static_callable(get_key)

    def processevent(self, event):
        """Event handler

        @param event event to handle
        """
        key = self.get_key(event.sock, event.match.dl_src)

        #Broadcast mac
        if (pu.is_multicast_mac(event.match.dl_src)):
            return True

        mc.set(key, event.pktin.in_port, mac2sw_binding.TIMEOUT)
        output.vdbg("Learn that %x " % pu.array2val(event.match.dl_src) +\
                       "is connected to port " + \
                       str(event.pktin.in_port)+" of switch with "+\
                       str(event.sock),
                   self.__class__.__name__)

        return True

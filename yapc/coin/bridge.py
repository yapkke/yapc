##COIN NAT
#
# Client-side OpenFlow Interface for Networking (Bridge Mode)
#
# @author ykk
# @date Sept 2011
#
import yapc.coin.core as core

class bridge(core.coin_server):
    """Class to handle connections and configuration for COIN in Bridge mode

    @author ykk
    @date Sept 2011
    """
    def __init__(self, server, ofconn, jsonconn):
        """Initialize

        @param server yapc core server/scheduler
        @param ofconn OpenFlow connections
        @param jsonconn JSON connections
        """
        core.coin_server.__init__(self, server, ofconn, jsonconn, False)
        ##Mode
        self.config["mode"] = "Multi-Homed (Bridged)"


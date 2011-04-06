##Host's internal state
#
# @author ykk
# @date Apr 2011
#
import dpkt
import socket
import yapc.interface as yapc
import yapc.output as output
import yapc.util.memcacheutil as mc
import yapc.util.parse as pu
import yapc.events.openflow as ofevents

class host_dns(yapc.component):
    """Class that sniffs name-ip address binding of host
    
    @author ykk
    @date Apr 2011
    """
    ##Key prefix for domain name
    HOST_DNS_DOMAIN_PREFIX = "dnshost_domain_"
    ##Key prefix for domain name
    HOST_DNS_IP_PREFIX = "dnshost_ip_"
    def __init__(self, server):
        """Initialize

        @param server yapc core
        """
        server.register_event_handler(ofevents.pktin.name, self)

    def get_name_key(host, domain_name):
        """Get key for domain name

        @param domain_name domain name
        """
        return host_dns.HOST_DNS_DOMAIN_PREFIX+\
            pu.array2hex_str(host)+"_"+domain_name
    get_name_key = yapc.static_callable(get_name_key)

    def get_addr_key(ipaddr):
        """Get key for IP address

        @param ipaddr IP address in value
        """
        return host_dns.HOST_DNS_IP_PREFIX+socket.inet_ntoa(ipaddr)
    get_addr_key = yapc.static_callable(get_addr_key)

    def processevent(self, event):
        """Handle event to sniff domain name-IP address binding
        """
        if (isinstance(event, ofevents.pktin)):
            if (event.match.tp_src == 53):
                try:
                    dnsreply = dpkt.dns.DNS(event.dpkt["data"]["data"]["data"])
                except:
                    return True
                nameaddr = {}

                for rr in dnsreply["an"]:
                    if (rr["type"] == 1):
                        #Record address for domain name
                        if (rr["name"] not in nameaddr):
                            nameaddr[rr["name"]] = []
                        nameaddr[rr["name"]].append(rr["rdata"])
                        #Record domain name for address
                        mc.set(host_dns.get_addr_key(rr["rdata"]), rr["name"], rr["ttl"])
                        output.vdbg("AN: "+socket.inet_ntoa(rr["rdata"])+" set to "+rr["name"]+\
                                        " with TTL "+str(rr["ttl"]),
                                    self.__class__.__name__)

                for rr in dnsreply["ar"]:
                    if (rr["type"] == 1):
                        #Record domain name for address
                        mc.set(host_dns.get_addr_key(rr["rdata"]), rr["name"], rr["ttl"])
                        output.vdbg("AR: "+socket.inet_ntoa(rr["rdata"])+" set to "+rr["name"]+\
                                        " with TTL "+str(rr["ttl"]),
                                    self.__class__.__name__)

                for name,val in nameaddr.items():
                    if (len(val) != 0):
                        mc.set(host_dns.get_name_key(event.match.dl_src, name), val)
                        output.dbg(name+"=>"+str(len(val))+" IP addresses",
                                   self.__class__.__name__)
                    


        return True
        

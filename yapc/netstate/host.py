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
    HOST_DNS__DOMAIN_PREFIX = "dnshost_domain_"
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
        return host_dns.HOST_DNS_DOMAIN_PREFIX+host+"_"+domain_name
    get_name_key = yapc.static_callable(get_name_key)

    def get_addr_key(ipaddr):
        """Get key for IP address

        @param ipaddr IP address in value
        """
        return host_dns.HOST_DNS_IP_PREFIX+ipaddr
    get_addr_key = yapc.static_callable(get_addr_key)

    def processevent(self, event):
        """Handle event to sniff domain name-IP address binding
        """
        if (isinstance(event, ofevents.pktin)):
            if (event.match.tp_src == 53):
                dnsreply = dpkt.dns.DNS(event.dpkt["data"]["data"]["data"])
                nameaddr = {}

                for q in dnsreply["qd"]:
                    nameaddr[q["name"]] = []

                for rtype in ["an","ar"]:
                    for rr in dnsreply[rtype]:
                        if (rtype == "an"):
                            nameaddr[rr["name"]].append(rr["rdata"])
                            
                        if (len(rr["rdata"]) == 4):
                            mc.set(host_dns.get_addr_key(socket.inet_ntoa(rr["rdata"])),
                                   rr["name"], rr["ttl"])
                            output.dbg(rtype+" record: "+\
                                           rr["name"]+" binded to "+socket.inet_ntoa(rr["rdata"])+\
                                           " with TTL of "+str(rr["ttl"])+ "s for host "+\
                                           pu.array2hex_str(event.match.dl_dst),
                                       self.__class__.__name__)
                        else:
                            output.dbg(rtype+" record: "+\
                                           rr["name"]+" binded to "+str(rr["rdata"])+\
                                           " with TTL of "+str(rr["ttl"])+ "s for host "+\
                                           pu.array2hex_str(event.match.dl_dst),
                                       self.__class__.__name__)

                for name,val in nameaddr.items():
                    output.dbg(name+"=>"+str(len(val))+" IP addresses",
                               self.__class__.__name__)

        return True
        

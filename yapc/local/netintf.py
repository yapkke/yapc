##Local network interface
#
# Control for local network interfaces
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.output as output
import netifaces
import os

IFCONFIG = "ifconfig"

class interfacemgr(yapc.cleanup):
    """Interface manager class to manage interfaces

    @author ykk
    @date Feb 2011
    """
    def __init__(self, server):
        """Initialize

        @param server yapc core
        """
        ##List of veth
        self.veth = []

        server.scheduler.registercleanup(self)

    def cleanup(self):
        """Clean up interfaces
        """
        output.dbg("Cleaning up veth interfaces",
                   self.__class__.__name__)
        for v in self.veth:
            v.__del__()

    def add_veth(self):
        """Add new veth pair
        """
        r = veth_pair()
        self.veth.append(r)
        return r

    def del_veth(self, veth):
        """Del veth pair
        """
        self.veth.remove(veth)
        del veth

    def interfaces(self):
        """Return interfaces
        @return interface names
        """
        return netifaces.interfaces()

    def ifaddresses(self, intf=None):
        """Return addresses for specified interface or all interfaces
        
        @param intf interface
        @return addresses or dictionary of addresses
        """
        if (intf == None):
            result = {}
            for i in self.interfaces():
                result[i] = netifaces.ifaddresses(i)
            return result
        else:
            return netifaces.ifaddresses(intf)

    def ethernet_ipv4_addresses(self, intf=None):
        """Return Ethernet + IPv4 addresses for specified interface or all interfaces
        
        @param intf interface
        @return Ethernet and IPv4  addresses
        """
        ifaddr = self.ifaddresses(intf)
        if (intf == None):
            result = {}
            for i,addr in ifaddr.items():
                if (netifaces.AF_PACKET in addr):
                    result[i] = self.__get_ethernet_ipv4_addr(addr)
        else:
            return self.__get_ethernet_ipv4_addr(ifaddr)
        return result
    
    def __get_ethernet_ipv4_addr(self, addr):
        """Extract Ethernet and IPv4 addresses
        
        @param addr addresses of a single interface
        @return dictionary of Ethernet and IPv4 addresses, None otherwise
        """
        result = {}
        if (netifaces.AF_PACKET in addr):
            result[netifaces.AF_PACKET] = addr[netifaces.AF_PACKET]
            if (netifaces.AF_INET in addr):
                result[netifaces.AF_INET] = addr[netifaces.AF_INET]
            return result
        else:
            return None

    def set_ipv4_addr(self, intf, addr, netmask=None):
        """Set IPv4 address
        
        @param intf interface name
        @param addr IPv4 address string
        @param netmask network mask string
        """
        c = IFCONFIG+" "+intf+" "+addr
        if (netmask != None):
            c += " netmask "+netmask
        cmd.run_cmd(c, self.__class__.__name__)

class veth_pair:
    """Class to create, manage and cleanup veth
    
    @author ykk
    @date Feb 2011
    """
    def __init__(self):
        """Initialize
        """
        ##Name of interfaces
        self.names = []
        oldi = netifaces.interfaces()
        os.system("ip link add type veth")
        newi = netifaces.interfaces()
        for i in newi:
            if (i not in oldi):
                self.names.append(i)
        output.dbg("Created virtual interfaces "+str(self.names),
                   self.__class__.__name__)

    def __del__(self):
        """Remove ip link
        """
        os.system("ip link del "+str(self.names[0]))
        output.dbg("Cleaning up "+str(self.names[0]),
                   self.__class__.__name__)


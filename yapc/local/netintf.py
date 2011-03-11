##Local network interface
#
# Control for local network interfaces
#
# @author ykk
# @date Feb 2011
#
import yapc.interface as yapc
import yapc.commands as cmd
import yapc.output as output
import netifaces
import os

IFCONFIG = "ifconfig"
DHCP = "dhclient"
ROUTE = "route"

class ipv4_addr_mgr:
    """Interface manager class to manage addresses for IPv4

    @author ykk
    @date Mar 2011
    """    
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
        @return result of command
        """
        c = IFCONFIG+" "+intf+" "+addr
        if (netmask != None):
            c += " netmask "+netmask
        return cmd.run_cmd(c, self.__class__.__name__)

    def invoke_dhcp(self, intf=None):
        """Invoke DHCP on interface or on all interfaces if intf=None

        @param intf interface to invoked DHCP on
        @return result of command
        """
        c = DHCP
        if (intf != None):
            c += " "+intf
        return cmd.run_cmd(c, self.__class__.__name__)

class route_entry_flags:
    """Route entry flags

    @author ykk
    @date Mar 2011
    """
    def __init__(self, flags=""):
        """Initialize
        """
        self.parse(flags)

    def parse(self, flags):
        """Parse flags
        """
        #Route is up
        self.up = False
        if (flags.find("U")  != -1):
            self.up = True
        #Target is host
        self.host = False
        if (flags.find("H")  != -1):
            self.host = True
        #Use gateway
        self.gateway = False
        if (flags.find("G")  != -1):
            self.gateway = True
        #Reinstate routing for dynamic routing
        self.reinstate = False
        if (flags.find("R")  != -1):
            self.reinstate = True
        #Dynamically installed by daemon/redirect
        self.dynamic = False
        if (flags.find("D")  != -1):
            self.dynamic = True
        #Modified by daemon or redirect
        self.modified = False
        if (flags.find("M")  != -1):
            self.modified = True
        #Installed by addrconf
        self.addrconf = False
        if (flags.find("A")  != -1):
            self.addrconf = True
        #Cache entry
        self.cache = False
        if (flags.find("C")  != -1):
            self.cache = True
        #Reject route
        self.reject = False
        if (flags.find("!")  != -1):
            self.reject = True

    def __str__(self):
        """Return string
        """
        s = ""
        if (self.up):
            s += "U"
        if (self.host):
            s += "H"
        if (self.gateway):
            s += "G"
        if (self.reinstate):
            s += "R"
        if (self.dynamic):
            s += "D"
        if (self.modified):
            s += "M"
        if (self.addrconf):
            s += "A"
        if (self.cache):
            s += "C"
        if (self.reject):
            s += "!"
        return s

class route_entry(route_entry_flags):
    """Route entry in routing table

    @author ykk
    @date Mar 2011
    """
    def __init__(self, entry_line=""):
        """Initalize
        """
        ##Destination
        self.destination = "0.0.0.0"
        ##Gateway
        self.gateway = "0.0.0.0"
        ##Mask
        self.mask = "0.0.0.0"
        ##Flags
        self.flags = route_entry_flags()
        ##Metric
        self.metric = 0
        ##Reference
        self.ref = 0
        ##Use
        self.use = 0
        ##Interface
        self.iface = ""
    
        if (entry_line != ""):
            self.parse(entry_line)

    def parse(self, entry_line):
        """Parse line
        """
        i = entry_line.split()
        if (len(i) != 8):
            output.warn("Route entry line should have 8 items but "+str(len(i))+" found",
                        self.__class__.__name__)
            return
        else:
            self.destination = i[0]
            self.gateway = i[1]
            self.mask = i[2]
            self.flags.parse(i[3])
            self.metric = int(i[4])
            self.ref = int(i[5])
            self.use = int(i[6])
            self.iface = i[7]

    def __str__(self):
        """Return string represention
        """
        return "Dest="+self.destination+\
            "\tGW="+self.gateway+\
            "\tMask="+self.mask+\
            "\tFlags="+str(self.flags)+\
            "\tMetric="+str(self.metric)+\
            "\tRef="+str(self.ref)+\
            "\tUse="+str(self.use)+\
            "\tIface="+self.iface

class route_mgr:
    """Manager for route on the device

    @author ykk
    @date Mar 2011
    """
    def __init__(self):
        """Initialize
        """
        self.__routes = []
        self.query_route()

    def query_route(self):
        """Query for current route
        """
        c = ROUTE+ " -n"
        (ret, out) = cmd.run_cmd(c, self.__class__.__name__)
        self.__routes = []
        for l in out[2:]:
            self.__routes.append(route_entry(l))
    
    def get_route(self):
        """Get currently cache route
        """
        return self.__routes[:]

    def get_gateways(self, intf=None):
        """Get all the gateway
        
        @param intf list of interfaces to get gateway for (if None, then return all)
        @return list of gateways
        """
        g = []
        for r in self.__routes:
            if (intf == None or r.iface in intf):
                if (r.flags.gateway and
                    r.gateway not in g):
                    g.append(r.gateway)
        return g

class interfacemgr(ipv4_addr_mgr, route_mgr, yapc.cleanup):
    """Interface manager class to manage interfaces

    @author ykk
    @date Feb 2011
    """
    def __init__(self, server):
        """Initialize

        @param server yapc core
        """
        route_mgr.__init__(self)
        ##List of veth
        self.veth = []

        server.register_cleanup(self)

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


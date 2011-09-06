##Module to provide packet source
#
import yapc.log.output as output
import pcap

class pcap_file:
    """Class to represent pcap file

    @author ykk
    @date Sept 2011
    """
    def __init__(self, filename=None, load=True):
        """Initialize

        @param filename filename of pcap file
        @param load load file or not
        """
        ##Reference to filename
        self.filename = filename
        ##Reference to packets
        self.packets = []
        ##Iterator
        self.__pcap_iter = None

        if (load):
            self.load()

    def load(self):
        """Load pcap file
        """
        pc = pcap.pcap(self.filename)
        for ts, pkt in pc:
            self.packets.append((ts, pkt))

    def get_next(self):
        """Get the next timestamp and packet

        @return (timestamp, packet) else None
        """
        if (self.__pcap_iter == None):
            self.__pcap_iter = iter(self.packets)
        try:
            return self.__pcap_iter.next() 
        except StopIteration:
            self.__pcap_iter = None
            return None

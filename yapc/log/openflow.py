import yapc.interface as yapc
import yapc.log.sqlite as sqlite
import yapc.events.openflow as ofevents

class flowlogger(sqlite.SqliteLogger, yapc.component):
    """Class to log flow removed

    @author ykk
    @date May 2011
    """
    def __init__(self, server, db, name="Flows"):
        """Initialize
        """
        sqlite.SqliteLogger.__init__(self, db, name) 
        server.register_event_handler(ofevents.flow_removed.name, self)

    def get_col_names(self):
        """Get column names
        """
        return ["cookie", "priority", "reason", "idle_timeout", "in_port",
                "dl_src", "dl_dst", "dl_type", "dl_vlan", "dl_vlan_pcp",
                "nw_src", "nw_dst", "nw_proto", "nw_tos",
                "tp_src", "tp_dst",
                "duration_sec", "duration_nsec", "packet_count", "byte_count"]

    def processevent(self, event):
        """Process event
        """
        if (isinstance(event, ofevents.flow_removed)):
            i = [event.flowrm.cookie, 
                 event.flowrm.priority,
                 event.flowrm.reason,
                 event.flowrm.idle_timeout,
                 event.flowrm.match.in_port,
                 event.flowrm.match.dl_src,
                 event.flowrm.match.dl_dst,
                 event.flowrm.match.dl_type,
                 event.flowrm.match.dl_vlan,
                 event.flowrm.match.dl_vlan_pcap,
                 event.flowrm.match.nw_src,
                 event.flowrm.match.nw_dst,
                 event.flowrm.match.nw_proto,
                 event.flowrm.match.nw_tos,
                 event.flowrm.match.tp_src,
                 event.flowrm.match.tp_dst,
                 event.flowrm.duration_sec,
                 event.flowrm.duration_nsec,
                 event.flowrm.packet_count,
                 event.flowrm.byte_count]
            self.table.add_row(tuple(i))

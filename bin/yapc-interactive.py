import yapc.core as core
import yapc.interface as yapc
import yapc.ofcomm as ofcomm
import yapc.output as output
import yapc.pyopenflow as pyopenflow
import yapc.interactive as interactive
import yapc.events.openflow as ofevents

output.set_mode("WARN")

#Create core and OpenFlow sockets
server = core.core()
ofconn = ofcomm.ofserver(server)
ofparse = ofevents.parser(server)
server.run(runbg=True)

#Create event queue
pktin_event = interactive.event_queue(server, ofevents.pktin.name)

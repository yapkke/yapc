#!/usr/bin/python
## Client OpenFlow Interface for Networking
# @author ykk
# @date Oct 2010
#
import yapc.core as core
import yapc.ofcomm as ofcomm
import yapc.jsoncomm as jsoncomm
import yapc.output as output
import yapc.coin.core as coin
import sys

#Set output mode
output.set_mode("DBG")

#Create yapc base
server = core.server()
ofcomm.ofserver().bind(server)
jsoncomm.jsonserver().bind(server)

#Create coin base
coinserver = coin.openflowhandler()
server.scheduler.registereventhandler(ofcomm.message.name,
                                      coinserver)
server.scheduler.registereventhandler(jsoncomm.message.name,
                                      coinserver)
#Start
#server.daemonize()
server.run()
sys.exit(0)

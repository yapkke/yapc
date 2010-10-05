#!/usr/bin/python
## Client OpenFlow Interface for Networking
# @author ykk
# @date Oct 2010
#
import yapc.core as core
import yapc.ofcomm as ofcomm
import yapc.output as output
import yapc.coin.core as coin
import sys

#Set output mode
output.set_mode("INFO")

#Create yapc base
server = core.server()
ofcomm.ofserver().bind(server)

#Create coin base
coinserver = coin.openflowhandler()
server.scheduler.registereventhandler(ofcomm.message.name,
                                      coinserver)
#Start
#server.daemonize()
server.run()
sys.exit(0)

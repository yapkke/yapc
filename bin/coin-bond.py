#!/usr/bin/python
## Client OpenFlow Interface for Networking (Bonding)
# @author ykk
# @date Oct 2010
#
import yapc.jsoncomm as jsoncomm
import simplejson
import sys
import time

sock = jsoncomm.client()
sock.sock.send("{\"testing\":1}")

time.sleep(1)
sys.exit(0)



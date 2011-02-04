"""\mainpage Yet Another Python Controller (YAPC) for OpenFlow

@author ykk
@date October 2010

This is a really simple Python controller.  The main event dispatcher
of the controller runs in a thread, separated from the receiving
thread.  You can use native Python threads as you wish.

The main interfaces are in
* yapc.interface -- for all the class you can inherit
* yapc.core --
     eventdispatcher for registercleanup and registereventhandler
"""

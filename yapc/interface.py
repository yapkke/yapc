##Interfaces for YAPC
#
# @author ykk
# @date Oct 2010
#

class event:
    """Base class for events

    @author ykk
    @date Oct 2010
    """
    ##Name
    name = None
        
class component:
    """Base component for events
   
    Should only stores soft state used internally.
    I would argue that all hard state should be done by
    on systems like memcached. YAPC's framework allows 
    you to shoot yourself in the foot nonetheless.

    @author ykk
    @date Oct 2010
    """
    def processevent(self, event):
        """Dummy function to process event

        @param event reference to event
        @return True for continue, else stop
        """
        return True

class cleanup:
    """Base component that handles shutdown

    @author ykk
    @date Oct 2010
    """
    def cleanup(self):
        """Dummy function to cleanup
        """
        return

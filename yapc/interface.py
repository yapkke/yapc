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
   
    Should only stores soft state used internally

    @author ykk
    @date Oct 2010
    """
    def processevent(self, event):
        """Dummy function to process event

        Return True for continue, else stop
        """
        raise RuntimeException("Component "+str(self.__class__.__name__)+\
                                   "has to override processevent function")

class infostore:
    """Base for information storage (hard state)
    
    @author ykk
    @date Oct 2010
    """
    def save(self):
        """Store information
        """
        raise RuntimeException("Component "+str(self.__class__.__name__)+\
                                   "has to override ssave function")

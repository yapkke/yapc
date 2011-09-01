##Basic JSON message
#
# @author ykk
# @date Aug 2011
#
import simplejson

class message:
    """JSON message

    @author ykk
    @date Aug 2011
    """
    def __init__(self, msg):
        """Initialize with JSON object
        """
        self.json_msg = simplejson.loads(msg)

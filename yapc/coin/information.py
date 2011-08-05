##Information plane for COIN

import yapc.interface as yapc

class core(yapc.component):
    """COIN's information plane.

    Allows the following to be done
    (1) query for stored information,
    (2) publish and subscribe for information, and
    (3) trigger (and return)

    To separate measurement for its retrieval.

    This component is actually a meta-component that invokes several
    other components, namely: 

    (1) pubsub which handles all publish and subscribe: taking events
    published and sending it to the subscribers (this is not needed if
    all information plane is within the same yapc core, since the
    event model provides this publish-subscribe mechanism already)

    (2) infolog which takes any query and send back the result: this
    component logs all event published and stores it for queries to
    come

    (3) probe which proxy a probe to a measurement component and
    returns the result: the component will match the information type
    with the components as needed.  Note that this should also result
    in a publish event containing the same information. (this is not
    needed if all information plane is within the same yapc core,
    since the event model provides this mechanism for probing already)

    @author ykk
    @date July 2011
    """
    def __init__(self, server):
        """Initialize
        """
        self.infolog = infolog(server)
        

class infolog(yapc.component):
    """Information logging facility that accepts queries.

    @author ykk
    @date August 2011
    """
    def __init__(self, server):
        """Initialize
        """
        self.server.register_event_handler(publish.name, self)

    def processevent(self, event):
        """Process publish and query events

        @param event Event to handler
        @return True
        """
        if isinstance(event, publish):
            #Publish event
            pass
        elif isinstance(event, query):
            #Query event
            pass

        return True       
    
class base(yapc.component):
    """Basic class for component that export information
   
    @author ykk
    @date August 2011
    """
    def eventname(self):
        """Provide name for event used to publish data
        
        @return list of event name
        """
        return []

class publish(yapc.event):
    """Basic event to publish data
    
    (To be inherited and overridden: name of event should not be
    changed.  However, event_specific name (eventname) should be
    changed.)

    Must provide key,value representation for storage

    @author ykk
    @date August 2011
    """
    name = "Publish event"
    eventname = "Basic"
    def get_dict(self):
        """Provide dict (with key, value pair) to represent event
       
        @return array of dict to represent event
        """
        return []

class subscribe(yapc.event):
    """Basic event to subscribe to data
    
    @author ykk
    @date August 2011
    """
    name = "Subscribe event"

class query(yapc.event):
    """Basic event to query for data

    @author ykk
    @date August 2011
    """
    name = "Query event"
    queryname = "Basic"

class probe(yapc.event):
    """Basic event to probe for data

    @author ykk
    @date August 2011
    """
    name = "Probe event"
    probename = "Basic"


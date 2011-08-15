##Information plane for COIN
import yapc.interface as yapc
import yapc.log.output as output
import yapc.log.sqlite as sqlite

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
        ##Reference to yapc's core
        self.server = server
        ##Reference to infolog
        self.infolog = infolog(server)

    def start(self):
        """Start database
        """
        self.infolog.db.start()
        
class infolog(yapc.component):
    """Information logging facility that accepts queries.

    @author ykk
    @date August 2011
    """
    def __init__(self, server, filename="coin.sqlite"):
        """Initialize
        """
        ##Reference to core
        self.server = server
        ##Referece to logger
        self.loggers = {}
        ##Database
        self.db = sqlite.SqliteDB(server, filename)

        self.server.register_event_handler(publish.name, self)

    def register_logger(self, name, logger):
        """Register logger for publish event in COIN

        @param name name of event
        @param logger logger to log event
        """
        self.loggers[name] = logger

    def processevent(self, event):
        """Process publish and query events

        @param event Event to handler
        @return True
        """
        if isinstance(event, publish):
            #Publish event
            try:
                logger = self.loggers[event.eventname]
            except KeyError:
                output.warn("No logger registered for "+event.eventname+"!",
                            self.__class__.__name__)
                return True

            for i in event.get_dict():
                d = []
                for k in logger.get_col_names():
                    d.append(i[k])
                logger.table.add_row(tuple(d))
                output.vdbg("Recorded measurement of "+str(i),
                            self.__class__.__name__)
                
        elif isinstance(event, query):
            #Query event
            output.dbg("Query "+str(event.get_query()),
                       self.__class__.__name__)

        return True       

class base(yapc.component,sqlite.SqliteLogger):
    """Basic class for component that export information

    @author ykk
    @date August 2011
    """
    def __init__(self, coin, loggername):
        """Initialize
        
        @param coin COIN's core
        @param name loggername of logger
        """
        sqlite.SqliteLogger.__init__(self, coin.infolog.db, loggername)
        coin.infolog.register_logger(self.eventname(), self)
        
    def get_col_names(self):
        """Get names of columns
        """
        output.warn("get_col_names should overloaded",
                    self.__class__.__name__)
        return []

    def eventname(self):
        """Provide name for event used to publish data
        
        @return event name
        """
        output.warn("eventname should overloaded",
                    self.__class__.__name__)
        return None

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
    keys = []
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
    def __init__(self, condition=None):
        """Initialize

        @param condition statement
        """
        ##Condition
        self.condition = condition

    def get_query(self):
        """Get SQL query to issue

        @return string with SQL query
        """
        return ""

class probe(yapc.event):
    """Basic event to probe for data

    @author ykk
    @date August 2011
    """
    name = "Probe event"
    probename = "Basic"


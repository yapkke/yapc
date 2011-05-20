##Module to handle SQLite3 interaction
#
# @uathor ykk
# @date May 2011
#
import sqlite3
import yapc.interface as yapc
import yapc.log.output as output

class Database:
    """SQLite database class

    @author ykk
    @date May 2011
    """
    def __init__(self, filename):
        """Initialize

        @param filename name of database file
        """
        ##Filename
        self.filename = filename
        ##Connection
        self.connection = None
        ##List of tables
        self.tables = {}

    def open(self):
        """Open database
        """
        if (self.connection == None):
            self.connection = sqlite3.connect(self.filename)
            output.dbg("Opening database "+self.filename)
            self.connection.row_factory = sqlite3.Row
        
    def close(self):
        """Close database
        """
        if (self.connection != None):
            output.dbg("Closing database")
            self.connection.commit()
            self.connection.close()
            self.connection = None

    def add_table(self, table):
        """Add table
        """
        self.tables[table.name] = table

    def create_tables(self, close=True):
        """Create tables in database
        """
        for tname,tab in self.tables.items():
            tab.create(self)
        self.close()

    def execute(self, stmt, close=True):
        """Execute statement
        """
        self.open()
        output.vdbg(stmt, self.__class__.__name__)
        r = self.connection.execute(stmt)
        if (close):
            self.close()
        return r

    def executemany(self, stmt, data, close=True):
        """Execute many statements
        """
        self.open()
        r = self.connection.executemany(stmt, data)
        if (close):
            self.close()
        return r

    def commit(self):
        """Commit commands
        """
        self.connection.commit()

    def flush(self):
        """Flush cache of all tables
        """
        for tname,tab in self.tables.items():
            tab.flush_cache()
        self.connection.commit()

class Table:
    """SQLite table

    @author ykk
    @date May 2011
    """
    def __init__(self, name, columns=None, cs=100):
        """Initialize

        @param name name of table
        @param columns list of column names
        @param cs max cache size to maintain
        """
        ##Name of table
        self.name = name
        ##Names of columns
        self.columns = columns
        if (columns == None):
            self.columns = []
        ##Cache of data to add
        self.data_cache = []
        ##Cache max
        self.cache_size = cs
        ##Reference to db
        self.db = None

    def add_column(self, name):
        """Add column with name
        """
        self.columns.append(name)

    def create_stmt(self, ine=True):
        """Return create statement

        @param ine add IF NOT EXISTS
        """
        r = "CREATE TABLE "
        if (ine):
            r+= "IF NOT EXISTS "
        r += self.name+"("
        for c in self.columns:
            r += c+","
        return r[:-1]+")"
    
    def create(self, db):
        """Create table in database

        @param db reference to database
        """
        self.db = db
        db.execute(self.create_stmt())

    def add_row(self, row):
        """Add data to the table

        @param row  is a tuple of data
        """
        if (len(row) == len(self.columns)):
            output.vdbg("Add row :"+str(row))
            self.data_cache.append(row)
            if (len(self.data_cache) >= self.cache_size):
                self.flush_cache()
        else:
            output.warn("Adding row "+str(row)+" with "+len(row)+" items"+\
                            " when there is "+len(self.columns)+" columns",
                        self.__class__.__name__)

    def flush_cache(self):
        """Flush data in cache in database
        """
        if (self.db == None):
            output.warn("No database to flush data into",
                        self.__class__.__name__)
            return

        stmt = "?,"*len(self.columns)
        self.db.executemany("INSERT INTO "+self.name+\
                                " VALUES ("+stmt[:-1]+")",
                            self.data_cache)
        self.data_cache = []

    def select_stmt(self, selection="*", where=None):
        """Create the following:
           SELECT <select> FROM <table> WHERE <where>

        @param selection selection to return
        @param where where condition
        """
        r = "SELECT "+selection+" FROM "+self.name
        if (where != None):
            r += "WHERE "+where
        return r

    def select(self, selection="*", where=None):
        """Execute the following:
           SELECT <select> FROM <table> WHERE <where>

        @param selection selection to return
        @param where where condition
        """
        return self.db.execute(self.select_stmt(selection, where))

class SqliteDB(Database, yapc.cleanup):
    """SQLite database with proper cleanup

    @author ykk
    @date May 2011
    """
    def __init__(self, server, filename):
        """Initialize
        """
        Database.__init__(self, filename)
        server.register_cleanup(self)
        self.started = False

    def start(self, close=True):
        """Start/setup the database

        @oaram close close connection after creating tables
        """
        self.create_tables(close)
        self.started = True

    def cleanup(self):
        """Clean up
        """
        output.dbg("Cleaning up database",
                   self.__class__.__name__)
        if (self.connection != None):
            self.flush()
            self.close()

class SqliteLogger:
    """Base class for loggers using SQLite database
    
    @author ykk
    @date May 2011
    """
    def __init__(self, db, name):
        """Initialize
        """
        self.name = name
        self.table = None

        if (db.started):
            output.err("Database "+str(db)+" is already started."+\
                           " Logger cannot be initialized!",
                       self.__class__.__name__)
        else:
            db.add_table(Table(name, self.get_col_names()))
            self.table = db.tables[name]

    def get_col_names(self):
        """Get names of columns
        """
        output.warn("get_col_names should overloaded",
                    self.__class__.__name__)
        return []

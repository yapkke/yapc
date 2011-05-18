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
        self.connection = sqlite3.connect(self.filename)
        output.dbg("Opening database "+self.filename)
        self.connection.row_factory = sqlite3.Row
        ##List of tables
        self.tables = {}

    def close(self):
        """Finalize
        """
        output.dbg("Closing database")
        self.flush()
        self.connection.commit()
        self.connection.close()

    def add_table(self, table):
        """Add table
        """
        self.tables[table.name] = table

    def create_tables(self):
        """Create tables in database
        """
        for tname,tab in self.tables.items():
            tab.create(self)
        self.connection.commit()

    def execute(self, stmt):
        """Execute statement
        """
        output.vdbg(stmt, self.__class__.__name__)
        return self.connection.execute(stmt)

    def executemany(self, stmt, data):
        """Execute many statements
        """
        return self.connection.executemany(stmt, data)

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
        self.db.commit()
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

class DB(Database, yapc.cleanup):
    """SQLite database with proper cleanup

    @author ykk
    @date May 2011
    """
    def __init__(self, server, filename):
        Database.__init__(self, filename)
        server.register_cleanup(self)

    def start(self):
        """Start/setup the database
        """
        self.create_tables()

    def cleanup(self):
        """Clean up
        """
        self.close()

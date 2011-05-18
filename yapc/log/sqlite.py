import sqlite3
import inspect
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
        self.connection.row_factory = sqlite3.Row
        ##List of tables
        self.tables = {}

    def __del__(self):
        """Finalize
        """
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

    def execute(self, stmt):
        """Execute statement
        """
        output.vdbg(stmt, self.__class__.__name__)
        self.connection.execute(stmt)

class Table:
    """SQLite table

    @author ykk
    @date May 2011
    """
    def __init__(self, name, columns=None):
        """Initialize

        @param name name of table
        @param columns list of column names
        """
        ##Name of table
        self.name = name
        ##Names of columns
        self.columns = columns
        if (columns == None):
            self.columns = []
    
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
        db.execute(self.create_stmt())

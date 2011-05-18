#!/usr/bin/env python

import yapc.log.output as output
import yapc.log.sqlite as sqlite

output.set_mode("VDBG")

db = sqlite.Database("testing.sqlite")
db.add_table(sqlite.Table("Test1", ["col1", "col2"]))
db.add_table(sqlite.Table("Test2", ["col12", "col22"]))
db.create_tables()




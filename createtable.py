import sqlite3

conn = sqlite3.connect('keepkeep.db')

conn.execute('''CREATE TABLE NOTES
         (ID INT PRIMARY KEY     NOT NULL,
         TITLE           TEXT,
         COLOR           TEXT,
         TEXTCONTENT     TEXT,
         LISTCONTENT     TEXT,
         ATTACHMENTS     TEXT,
         ANNOTATIONS     TEXT,
         EDITED          DATETIME,
         CREATED         DATETIME,
         ISTRASHED       BOOL,
         ISPINNED        BOOL,
         ISARCHIVED      BOOL);''')

conn.close()
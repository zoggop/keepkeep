import json
import sys
import os
import pathlib
import sqlite3
import zipfile
from datetime import datetime

if len(sys.argv) < 2:
	exit()

basePath = os.path.expanduser('~/keepkeep')
dbFilepath = basePath + '/keepkeep.db'

conn = sqlite3.connect(dbFilepath)

# reset table
conn.execute('''DROP TABLE NOTES''')
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

takeoutZip = sys.argv[1]
with zipfile.ZipFile(takeoutZip, 'r') as zf:
	srcPath = zipfile.Path(zf, 'Takeout/Keep/')
	files = srcPath.iterdir()
	i = 0
	for filepath in files:
		suffixes = filepath.name.split('.')
		if suffixes[-1] == 'json':
			print(filepath.name)
			b = filepath.read_bytes()
			e = json.loads(b.decode('utf-8'))
			sqlA = 'INSERT INTO NOTES (ID,'
			sqlB = 'VALUES ({},'.format(i)
			for k in e.keys():
				v = e.get(k)
				if k == 'userEditedTimestampUsec' or k == 'createdTimestampUsec':
					v = datetime.fromtimestamp(round(v / 1000000))
				elif type(v) != bool and type(v) != str:
					v = json.dumps(v)
				e[k] = v
				if k == 'userEditedTimestampUsec':
					sqlA += 'EDITED,'
				elif k == 'createdTimestampUsec':
					sqlA += 'CREATED,'
				else:
					sqlA += k.upper() + ','
				if type(v) == bool:
					sqlB += '{},'.format(v)
				elif type(v) == str:
					sqlB += "'{}',".format(v.replace("'", "''"))
				else:
					sqlB += "'{}',".format(v)
			sql = sqlA[:-1] + ') ' + sqlB[:-1] + ');'
			# print(sql)
			conn.execute(sql)
			i += 1

conn.commit()

conn.close()
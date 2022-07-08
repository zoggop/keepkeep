import json
import sys
import os
import pathlib
import sqlite3
from datetime import datetime

if len(sys.argv) < 2:
	exit()

basePath = os.path.expanduser('~/keepkeep')
dbFilepath = basePath + '/keepkeep.db'

conn = sqlite3.connect(dbFilepath)

sourceDir = sys.argv[1]
srcPath = pathlib.Path(sourceDir).expanduser()
files = srcPath.glob('*.json')
i = 0
for filepath in files:
	# print(filepath)
	with open(filepath, "rb") as read_file:
		b = read_file.read()
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
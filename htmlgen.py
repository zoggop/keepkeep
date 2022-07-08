import os
import pathlib
import sqlite3
import json
from shutil import copy2
from datetime import datetime

basePath = os.path.expanduser('~/keepkeep')
dbFilepath = basePath + '/keepkeep.db'
takeoutPath = os.path.expanduser('~/Documents/takeout/Keep')

imgExts = ['.jpg', '.png']

conn = sqlite3.connect(dbFilepath)

def yearMonthFormat(ym):
	ymDT = datetime.strptime(ym, "%Y-%m")
	return ymDT.strftime("%B %Y")

def paragrapher(txt):
	if txt is None:
		return
	lines = txt.split("\n")
	html = ''
	for l in lines:
		html += "<p>{}</p>\n".format(l)
	return html[:-1]

def loadChecklist(jsonTxt):
	cList = json.loads(jsonTxt)
	cHtml = "<ul>\n"
	for c in cList:
		check = '&#9744;'
		if c.get('isChecked') == True:
			check = '&#9745;'
		cHtml += "<li>{} {}</li>\n".format(check, c.get('text'))
	return cHtml[:-1]

def loadAttachments(jsonTxt):
	aList = json.loads(jsonTxt)
	aHtml = ''
	for a in aList:
		imgFilename = a.get('filePath')
		ext = imgFilename.split('.')[-1]						
		ei = 0
		while not os.path.exists(takeoutPath + '/' + imgFilename) and ei < len(imgExts):
			newExt = imgExts[ei]
			parts = imgFilename.split('.')
			imgFilename = '.'.join(parts[:-1]) + newExt
			ei += 1
		if os.path.exists(takeoutPath + '/' + imgFilename):
			copy2(takeoutPath + '/' + imgFilename, basePath + '/' + imgFilename)
			aHtml += "<img src='{}'>\n".format(imgFilename)
		else:
			print("file not found", a.get('filePath'))
	return aHtml[:-1]

def fetchMonth(yearMonth):
	cur = conn.cursor()
	cur.execute("SELECT * FROM NOTES WHERE CREATED BETWEEN '{}-01' AND '{}-31' AND ISARCHIVED = '0' AND ISTRASHED = '0' ORDER BY CREATED ASC".format(yearMonth, yearMonth))
	return cur.fetchall()

def generateMonthPage(yearMonth, prevYearMonth, nextYearMonth):
	rows = fetchMonth(yearMonth)
	contentHtml = ''
	for r in rows:
		noteHtml = noteTempl
		for ci in range(0, len(columns)):
			c = columns[ci]
			v = r[ci]
			if v is None:
				v = ''
			elif c == 'CREATED' or c == 'EDITED':
				dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
				v = dt.strftime("%A %#d, %I:%M %p")
			elif c == 'TEXTCONTENT':
				v = paragrapher(v)
			elif c == 'LISTCONTENT':
				v = loadChecklist(v)
			elif c == 'ATTACHMENTS':
				v = loadAttachments(v)
			noteHtml = noteHtml.replace('%{}%'.format(c), str(v))
		contentHtml += noteHtml + '\n\n'
	pageHtml = pageTempl
	pageHtml = pageHtml.replace('%CONTENT%', contentHtml)
	pageHtml = pageHtml.replace('%DATERANGE%', yearMonthFormat(yearMonth))
	if not prevYearMonth is None:
		pageHtml = pageHtml.replace('%PREVPAGE%', prevYearMonth)
		pageHtml = pageHtml.replace('%PREVDATE%', yearMonthFormat(prevYearMonth))
	if not nextYearMonth is None:
		pageHtml = pageHtml.replace('%NEXTPAGE%', nextYearMonth)
		pageHtml = pageHtml.replace('%NEXTDATE%', yearMonthFormat(nextYearMonth))
	with open('{}/{}.html'.format(basePath, yearMonth), 'w', encoding='utf-8') as write_file:
		write_file.write(pageHtml)

with open('note-template.html', "r") as read_file:
	noteTempl = read_file.read()
with open('page-template.html', "r") as read_file:
	pageTempl = read_file.read()

cur = conn.cursor()
data = cur.execute("SELECT * FROM NOTES")
columns = []
for c in data.description:
	columns.append(c[0])

cur = conn.cursor()
cur.execute("SELECT CREATED FROM NOTES WHERE ISARCHIVED = '0' AND ISTRASHED = '0' ORDER BY CREATED ASC")
rows = cur.fetchall()
months = {}
for r in rows:
	ym = r[0][:7]
	months[ym] = True
monthList = []
for ym in months.keys():
	monthList.append(ym)

for mi in range(0, len(monthList)):
	ym = monthList[mi]
	pym = None
	nym = None
	if mi != 0:
		pym = monthList[mi-1]
	if mi != len(monthList)-1:
		nym = monthList[mi+1]
	generateMonthPage(ym, pym, nym)

copy2('style.css', basePath + '/style.css')
copy2('color.css', basePath + '/color.css')

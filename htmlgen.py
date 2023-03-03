import os
import sys
import pathlib
import sqlite3
import json
import zipfile
from shutil import copy2
from datetime import datetime
from math import ceil

if len(sys.argv) < 2:
	exit()
takeoutZip = sys.argv[1]

basePath = os.path.expanduser('~/keepkeep')
dbFilepath = basePath + '/keepkeep.db'

imgExts = ['.jpg', '.png']

colorOrder = ['DEFAULT', 'RED', 'ORANGE', 'YELLOW', 'GREEN', 'TEAL', 'BLUE', 'CERULEAN', 'PURPLE', 'PINK', 'BROWN', 'GRAY']

maxMonthlyWordCount = 0

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
	zf = zipfile.ZipFile(takeoutZip, 'r')
	for a in aList:
		imgFilename = a.get('filePath')
		ext = imgFilename.split('.')[-1]						
		ei = 0
		while not zipfile.Path(zf, 'Takeout/Keep/' + imgFilename).exists() and ei < len(imgExts):
			newExt = imgExts[ei]
			parts = imgFilename.split('.')
			imgFilename = '.'.join(parts[:-1]) + newExt
			ei += 1
		if zipfile.Path(zf, 'Takeout/Keep/' + imgFilename).exists():
			p = zipfile.Path(zf, 'Takeout/Keep/' + imgFilename)
			print(p)
			with zipfile.ZipFile(takeoutZip, 'r') as zzf:
				with zzf.open('Takeout/Keep/' + imgFilename) as myfile:
					b = myfile.read()
			with open(basePath + '/' + imgFilename, 'wb') as binary_file:
				binary_file.write(b)
			aHtml += "<img src='{}'>\n".format(imgFilename)
		else:
			print("file not found", a.get('filePath'))
	return aHtml[:-1]

def loadAnnotations(jsonTxt):
	list = json.loads(jsonTxt)
	html = ''
	for a in list:
		html += "<div class='annotation'>\n<h4 class='annotationtitle'><a href='{}'>{}</a></h4>\n<p class='annotationdescription'>{}</p>\n</div>\n".format(a.get('url'), a.get('title'), a.get('description'))
	return html[:-1]

def fetchMonth(yearMonth):
	cur = conn.cursor()
	cur.execute("SELECT * FROM NOTES WHERE CREATED BETWEEN '{}-01' AND '{}-31' AND ISARCHIVED = '0' AND ISTRASHED = '0' ORDER BY CREATED ASC".format(yearMonth, yearMonth))
	return cur.fetchall()

def generateMonthPage(yearMonth, prevYearMonth, nextYearMonth):
	global maxMonthlyWordCount
	rows = fetchMonth(yearMonth)
	contentHtml = ''
	wordCount, noteCount = 0, 0
	colorCount = {}
	colorWords = {}
	for r in rows:
		noteHtml = noteTempl
		words = 0
		for ci in range(0, len(columns)):
			c = columns[ci]
			v = r[ci]
			if v is None:
				v = ''
			elif c == 'CREATED' or c == 'EDITED':
				dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
				v = dt.strftime("%A, %B %#d, %Y, %#I:%M %p")
			elif c == 'TEXTCONTENT':
				words = len(v.split())
				wordCount += words
				v = paragrapher(v)
			elif c == 'LISTCONTENT':
				v = loadChecklist(v)
			elif c == 'ATTACHMENTS':
				v = loadAttachments(v)
			elif c == 'ANNOTATIONS':
				v = loadAnnotations(v)
			elif c == 'COLOR':
				color = v
			noteHtml = noteHtml.replace('%{}%'.format(c), str(v))
		colorCount[color] = (colorCount.get(color) or 0) + 1
		colorWords[color] = (colorWords.get(color) or 0) + words
		contentHtml += noteHtml + '\n\n'
		noteCount += 1
	if wordCount > maxMonthlyWordCount:
		maxMonthlyWordCount = wordCount
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
	return { 'words': wordCount, 'notes': noteCount, 'colors': colorWords }

def generateOverviewPage(years, stats):
	contHtml = '<table class="overviewtable">\n'
	for y in years.keys():
		contHtml += '<tr class="overviewyear">\n<td><h2>{}</h2></td>\n</tr>\n'.format(y)
		for ym in years[y]:
			dt = datetime.strptime(ym, "%Y-%m")
			mname = dt.strftime("%B")
			colorCount = stats.get(ym).get('colors')
			maxCount = colorCount.get('max')
			colorChart = '<table class="colorchart"><tr>'
			for color in colorOrder:
				count = colorCount.get(color)
				if not count is None:
					blocks = ceil((count / maxMonthlyWordCount) * 100)
					colorChart += '<td class="count {}">{}</td>'.format(color, '-' * blocks)
			colorChart += '</tr></table>'
			contHtml += '<tr class="overviewmonth">\n<td><h3><a href="{}.html">{}</a></h3></td>\n<td>{:,} words</td>\n<td>{:,} notes</td>\n<td>{}</td>\n</tr>\n'.format(ym, mname, stats.get(ym).get('words'), stats.get(ym).get('notes'), colorChart)
	contHtml += '</table>'
	html = overTempl
	html = html.replace('%CONTENT%', contHtml)
	with open('{}/index.html'.format(basePath), 'w', encoding='utf-8') as write_file:
		write_file.write(html)


with open('note-template.html', "r") as read_file:
	noteTempl = read_file.read()
with open('page-template.html', "r") as read_file:
	pageTempl = read_file.read()
with open('overview-template.html', "r") as read_file:
	overTempl = read_file.read()

cur = conn.cursor()
data = cur.execute("SELECT * FROM NOTES")
columns = []
for c in data.description:
	columns.append(c[0])

cur = conn.cursor()
cur.execute("SELECT CREATED FROM NOTES WHERE ISARCHIVED = '0' AND ISTRASHED = '0' ORDER BY CREATED ASC")
rows = cur.fetchall()
months = {}
years = {}
for r in rows:
	ym = r[0][:7]
	y = int(r[0][:4])
	months[ym] = True
	years[y] = []
monthList = []
for ym in months.keys():
	monthList.append(ym)
	y = int(ym[:4])
	years[y].append(ym)

stats = {}
for mi in range(0, len(monthList)):
	ym = monthList[mi]
	pym = None
	nym = None
	if mi != 0:
		pym = monthList[mi-1]
	if mi != len(monthList)-1:
		nym = monthList[mi+1]
	stats[ym] = generateMonthPage(ym, pym, nym)

generateOverviewPage(years, stats)

copy2('style.css', basePath + '/style.css')
copy2('color.css', basePath + '/color.css')

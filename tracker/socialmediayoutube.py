import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

import MySQLdb
import MySQLdb.cursors
import datetime
from tracker.models import SocialMediaYoutube, Handle, YoutubeDailyNums
from django.db import IntegrityError
import pprint
pp = pprint.PrettyPrinter(indent=4)

db = MySQLdb.connect(host='localhost', user='theseus', passwd='theseus123',
						db='theseus_social', charset='utf8',
						cursorclass=MySQLdb.cursors.DictCursor)
todaydate = datetime.datetime.today().date()

def getvideostats(handle, gobackdays = 7):
	sincedate = todaydate - datetime.timedelta(days = gobackdays)
	since = sincedate
	until = todaydate
	cursor = db.cursor()
	query = "select sum(views) as views, sum(comments) as comments, count(1) as videos,"+\
		" sum(likes) as likes, sum(dislikes) as dislikes, date(published) as videodate"+\
		" from tracker_youtubechannelvideo where handle_id = %s and"+\
		" published >= '%s 00:00:00' and published <= '%s 23:59:59' group by videodate"
	query = query%(handle.id, since, until)
	# print query
	cursor.execute(query)
	count = 0
	rows = cursor.fetchall()
	daywiserows = {}
	for r in rows:
		daywiserows[r['videodate']] = {}
		daywiserows[r['videodate']]['videos'] = r['videos']
		daywiserows[r['videodate']]['views'] = r['views']
		daywiserows[r['videodate']]['comments'] = r['comments']
		daywiserows[r['videodate']]['likes'] = r['likes']
		daywiserows[r['videodate']]['dislikes'] = r['dislikes']
	cursor.close()
	# pp.pprint(daywiserows)
	return daywiserows

def saveyoutubesummary(handle, handle_stats):
	for daystats in handle_stats:
		try:
			SocialMediaYoutube(**daystats).save()
			print "Saved for date %s"%(daystats['reportdate'])
		except IntegrityError:
			s = SocialMediaYoutube.objects.filter(handle_id=daystats['handle_id'], reportdate=daystats['reportdate']).update(**daystats)
			print "Updated for date %s"%(daystats['reportdate'])
		except Exception as e:
			print e
	print "Summerized Youtube for HANDLE %s until %s"%(handle.name, todaydate)

def getchannelnumbers(handle, addedtime, field = "subscribers"):
	try:
		dailynums = YoutubeDailyNums.objects.get(handle_id = handle.id, addedtime = addedtime)
		if field == "subscribers":
			fieldnumbers = dailynums.subscribers
		elif field == "views":
			fieldnumbers = dailynums.views
	except YoutubeDailyNums.DoesNotExist:
		fieldnumbers = None
	return fieldnumbers


if __name__ == '__main__':
	gobackdays = 7
	datelist = [(todaydate - datetime.timedelta(days = days)) for days in range(gobackdays)]
	ythandles = Handle.objects.filter(platform_id = 3, status = 1)
	for handle in ythandles:
		print "\nHANDLE ==> %s %s"%(handle.id, handle.name)
		print "DATERANGE: %s to %s"%(datelist[-1], datelist[0])
		handlevideo_stats = getvideostats(handle, gobackdays)
		handle_stats = []
		for day in datelist:
			reportdate = day.strftime('%Y-%m-%d')
			reportdatebefore = (day - datetime.timedelta(days = 1)).strftime('%Y-%m-%d')
			subscribers_today = getchannelnumbers(handle, reportdate)
			subscribers_yday = getchannelnumbers(handle, reportdatebefore)

			views_today = getchannelnumbers(handle, reportdate, "views")
			views_yday = getchannelnumbers(handle, reportdatebefore, "views")

			try:
				newsubscribers = subscribers_today - subscribers_yday
				newviews = views_today - views_yday
			except:
				newsubscribers = 0
				newviews = 0
				print "Dailynums not found for daterange %s - %s"%(reportdate, reportdatebefore)
				
			tempdict = {}
			tempdict['handle_id'] = handle.id
			tempdict['reportdate'] = day

			tempdict['newsubscribers'] = newsubscribers
			tempdict['newviews'] = newviews

			if subscribers_today != None:
				tempdict['subscribers'] = subscribers_today
				tempdict['alltimeviews'] = views_today
			else:
				tempdict['subscribers'] = 0
				tempdict['alltimeviews'] = 0

			try:
				tempdict['views'] = handlevideo_stats[day]['views']
			except KeyError:
				tempdict['views'] = 0

			try:
				tempdict['comments'] = handlevideo_stats[day]['comments']
			except KeyError:
				tempdict['comments'] = 0

			try:
				tempdict['likes'] = handlevideo_stats[day]['likes']
			except KeyError:
				tempdict['likes'] = 0 

			try:
				tempdict['dislikes'] = handlevideo_stats[day]['dislikes']
			except KeyError:
				tempdict['dislikes'] = 0 

			try:
				tempdict['videos'] = handlevideo_stats[day]['videos']
			except KeyError:
				tempdict['videos'] = 0 

			handle_stats.append(tempdict)
			# pp.pprint(tempdict)

		saveyoutubesummary(handle, handle_stats)

	db.close()




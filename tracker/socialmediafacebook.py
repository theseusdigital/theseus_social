import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

import MySQLdb
import MySQLdb.cursors
import datetime
from tracker.models import SocialMediaFacebook, Handle, FacebookDailyNums
from django.db import IntegrityError
import pprint
pp = pprint.PrettyPrinter(indent=4)

db = MySQLdb.connect(host='localhost', user='theseus', passwd='theseus123',
						db='theseus_social', charset='utf8',
						cursorclass=MySQLdb.cursors.DictCursor)
todaydate = datetime.datetime.today().date()

def getpoststats(handle, gobackdays = 7, fanpost = 0):
	sincedate = todaydate - datetime.timedelta(days = gobackdays)
	since = sincedate
	until = todaydate
	cursor = db.cursor()
	query = "select sum(likes) as postlikes, sum(comments) as postcomments, sum(shares) as postshares,count(1) as postsnum,"+\
		" date(published) as postdate from tracker_facebookhandlepost where handle_id = %s and"+\
		" published >= '%s 00:00:00' and published <= '%s 23:59:59' and fanpost = %s group by postdate"
	query = query%(handle.id, since, until, fanpost)
	# print query
	cursor.execute(query)
	count = 0
	rows = cursor.fetchall()
	daywiserows = {}
	for r in rows:
		daywiserows[r['postdate']] = {}
		daywiserows[r['postdate']]['postlikes'] = r['postlikes']
		daywiserows[r['postdate']]['postcomments'] = r['postcomments']
		daywiserows[r['postdate']]['postshares'] = r['postshares']
		daywiserows[r['postdate']]['postsnum'] = r['postsnum']
	cursor.close()
	# pp.pprint(daywiserows)
	return daywiserows

def savefacebooksummary(handle, handle_stats):
	for daystats in handle_stats:
		try:
			SocialMediaFacebook(**daystats).save()
			print "Saved for date %s"%(daystats['reportdate'])
		except IntegrityError:
			s = SocialMediaFacebook.objects.filter(handle_id=daystats['handle_id'], reportdate=daystats['reportdate']).update(**daystats)
			print "Updated for date %s"%(daystats['reportdate'])
		except Exception as e:
			print e
	print "Summerized Facebook for HANDLE %s until %s"%(handle.name, todaydate)

def getpagelikes(handle, addedtime):
	try:
		dailynums = FacebookDailyNums.objects.get(handle_id = handle.id, addedtime = addedtime)
		pagelikes = dailynums.likes
	except FacebookDailyNums.DoesNotExist:
		pagelikes = None
	return pagelikes


if __name__ == '__main__':
	starttime = datetime.datetime.now()
	print sys.argv
	if(len(sys.argv)>1):
		gobackdays = int(sys.argv[1])
	else:
		gobackdays = 7
	datelist = [(todaydate - datetime.timedelta(days = days)) for days in range(gobackdays)]
	fbhandles = Handle.objects.filter(platform_id = 1, status = 1)
	for handle in fbhandles:
		print "\nHANDLE ==> %s %s"%(handle.id, handle.name)
		print "DATERANGE: %s to %s"%(datelist[-1], datelist[0])
		brandpost_stats = getpoststats(handle, gobackdays, 0)
		fanpost_stats = getpoststats(handle, gobackdays, 1)
		handle_stats = []
		for day in datelist:
			reportdate = day.strftime('%Y-%m-%d')
			reportdatebefore = (day - datetime.timedelta(days = 1)).strftime('%Y-%m-%d')
			pagelikes_today = getpagelikes(handle, reportdate)
			pagelikes_yday = getpagelikes(handle, reportdatebefore)

			try:
				newpagelikes = pagelikes_today - pagelikes_yday
			except:
				newpagelikes = 0
				print "Dailynums not found for daterange %s - %s"%(reportdate, reportdatebefore)
				
			tempdict = {}
			tempdict['handle_id'] = handle.id
			tempdict['reportdate'] = day

			tempdict['newpagelikes'] = newpagelikes
			if pagelikes_today != None:
				tempdict['pagelikes'] = pagelikes_today
			else:
				tempdict['pagelikes'] = 0

			try:
				tempdict['postlikes'] = brandpost_stats[day]['postlikes']
			except KeyError:
				tempdict['postlikes'] = 0 

			try:
				tempdict['comments'] = brandpost_stats[day]['postcomments']
			except KeyError:
				tempdict['comments'] = 0 

			try:
				tempdict['shares'] = brandpost_stats[day]['postshares']
			except KeyError:
				tempdict['shares'] = 0 

			try:
				tempdict['brandposts'] = brandpost_stats[day]['postsnum']
			except KeyError:
				tempdict['brandposts'] = 0

			try:
				tempdict['fanposts'] = fanpost_stats[day]['postsnum']
			except KeyError:
				tempdict['fanposts'] = 0
			handle_stats.append(tempdict)
			# pp.pprint(tempdict)

		savefacebooksummary(handle, handle_stats)

	db.close()
	endtime = datetime.datetime.now() - starttime
	print "Completed in {0} secs.".format(endtime.seconds)




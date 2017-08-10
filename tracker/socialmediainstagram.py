import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

import MySQLdb
import MySQLdb.cursors
import datetime
from tracker.models import SocialMediaInstagram, Handle, InstagramDailyNums
from django.db import IntegrityError
import pprint
pp = pprint.PrettyPrinter(indent=4)

db = MySQLdb.connect(host='localhost', user='theseus', passwd='theseus123',
						db='theseus_social', charset='utf8',
						cursorclass=MySQLdb.cursors.DictCursor)
todaydate = datetime.datetime.today().date()

def getpoststats(handle, gobackdays = 7):
	sincedate = todaydate - datetime.timedelta(days = gobackdays)
	since = sincedate
	until = todaydate
	cursor = db.cursor()
	query = "select sum(likes) as postlikes, sum(comments) as postcomments, count(1) as postsnum,"+\
		" date(published) as postdate from tracker_instagramhandlepost where handle_id = %s and"+\
		" published >= '%s 00:00:00' and published <= '%s 23:59:59' group by postdate"
	query = query%(handle.id, since, until)
	# print query
	cursor.execute(query)
	count = 0
	rows = cursor.fetchall()
	daywiserows = {}
	for r in rows:
		daywiserows[r['postdate']] = {}
		daywiserows[r['postdate']]['postlikes'] = r['postlikes']
		daywiserows[r['postdate']]['postcomments'] = r['postcomments']
		daywiserows[r['postdate']]['postsnum'] = r['postsnum']
	cursor.close()
	# pp.pprint(daywiserows)
	return daywiserows

def saveinstagramsummary(handle, handle_stats):
	for daystats in handle_stats:
		try:
			SocialMediaInstagram(**daystats).save()
			print "Saved for date %s"%(daystats['reportdate'])
		except IntegrityError:
			s = SocialMediaInstagram.objects.filter(handle_id=daystats['handle_id'], reportdate=daystats['reportdate']).update(**daystats)
			print "Updated for date %s"%(daystats['reportdate'])
		except Exception as e:
			print e
	print "Summerized Instagram for HANDLE %s until %s"%(handle.name, todaydate)

def getfollowers(handle, addedtime):
	try:
		dailynums = InstagramDailyNums.objects.get(handle_id = handle.id, addedtime = addedtime)
		followers = dailynums.followers
	except InstagramDailyNums.DoesNotExist:
		followers = None
	return followers

if __name__ == '__main__':
	starttime = datetime.datetime.now()
	print sys.argv
	if(len(sys.argv)>1):
		gobackdays = int(sys.argv[1])
	else:
		gobackdays = 7
	datelist = [(todaydate - datetime.timedelta(days = days)) for days in range(gobackdays)]
	ighandles = Handle.objects.filter(platform_id = 4, status = 1)
	for handle in ighandles:
		print "\nHANDLE ==> %s %s"%(handle.id, handle.name)
		print "DATERANGE: %s to %s"%(datelist[-1], datelist[0])
		brandpost_stats = getpoststats(handle, gobackdays)
		handle_stats = []
		for day in datelist:
			reportdate = day.strftime('%Y-%m-%d')
			reportdatebefore = (day - datetime.timedelta(days = 1)).strftime('%Y-%m-%d')
			followers_today = getfollowers(handle, reportdate)
			followers_yday = getfollowers(handle, reportdatebefore)

			try:
				newfollowers = followers_today - followers_yday
			except:
				newfollowers = 0
				print "Dailynums not found for daterange %s - %s"%(reportdate, reportdatebefore)
				
			tempdict = {}
			tempdict['handle_id'] = handle.id
			tempdict['reportdate'] = day

			tempdict['newfollowers'] = newfollowers
			if followers_today != None:
				tempdict['followers'] = followers_today
			else:
				tempdict['followers'] = 0

			try:
				tempdict['likes'] = brandpost_stats[day]['postlikes']
			except KeyError:
				tempdict['likes'] = 0 

			try:
				tempdict['comments'] = brandpost_stats[day]['postcomments']
			except KeyError:
				tempdict['comments'] = 0 

			try:
				tempdict['posts'] = brandpost_stats[day]['postsnum']
			except KeyError:
				tempdict['posts'] = 0

			handle_stats.append(tempdict)
			# pp.pprint(tempdict)

		saveinstagramsummary(handle, handle_stats)

	db.close()
	endtime = datetime.datetime.now() - starttime
	print "Completed in {0} secs.".format(endtime.seconds)




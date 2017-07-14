import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

import MySQLdb
import MySQLdb.cursors
import datetime
from tracker.models import SocialMediaTwitter, Handle, TwitterDailyNums
from django.db import IntegrityError
import pprint
pp = pprint.PrettyPrinter(indent=4)

db = MySQLdb.connect(host='localhost', user='nishant', passwd='nishu92',
						db='theseus_social', charset='utf8',
						cursorclass=MySQLdb.cursors.DictCursor)
todaydate = datetime.datetime.today().date()

def gettweetstats(handle, gobackdays = 7):
	sincedate = todaydate - datetime.timedelta(days = gobackdays)
	since = sincedate
	until = todaydate
	cursor = db.cursor()
	query = "select sum(favorite_count) as favorites, sum(retweet_count) as retweets, count(1) as tweets,"+\
		" date(created_at) as tweetdate from tracker_handletweet where handle_id = %s and"+\
		" created_at >= '%s 00:00:00' and created_at <= '%s 23:59:59' group by tweetdate"
	query = query%(handle.id, since, until)
	# print query
	cursor.execute(query)
	count = 0
	rows = cursor.fetchall()
	daywiserows = {}
	for r in rows:
		daywiserows[r['tweetdate']] = {}
		daywiserows[r['tweetdate']]['tweets'] = r['tweets']
		daywiserows[r['tweetdate']]['retweets'] = r['retweets']
		daywiserows[r['tweetdate']]['favorites'] = r['favorites']
	cursor.close()
	# pp.pprint(daywiserows)
	return daywiserows

def savetwittersummary(handle, handle_stats):
	for daystats in handle_stats:
		try:
			SocialMediaTwitter(**daystats).save()
			print "Saved for date %s"%(daystats['reportdate'])
		except IntegrityError:
			s = SocialMediaTwitter.objects.filter(handle_id=daystats['handle_id'], reportdate=daystats['reportdate']).update(**daystats)
			print "Updated for date %s"%(daystats['reportdate'])
		except Exception as e:
			print e
	print "Summerized Twitter for HANDLE %s until %s"%(handle.name, todaydate)

def getfollowers(handle, addedtime):
	try:
		dailynums = TwitterDailyNums.objects.get(handle_id = handle.id, addedtime = addedtime)
		followers = dailynums.followers
	except TwitterDailyNums.DoesNotExist:
		followers = None
	return followers


if __name__ == '__main__':
	gobackdays = 7
	datelist = [(todaydate - datetime.timedelta(days = days)) for days in range(gobackdays)]
	twhandles = Handle.objects.filter(platform_id = 2, status = 1)
	for handle in twhandles:
		print "\nHANDLE ==> %s %s"%(handle.id, handle.name)
		print "DATERANGE: %s to %s"%(datelist[-1], datelist[0])
		handletweet_stats = gettweetstats(handle, gobackdays)
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
				tempdict['retweets'] = handletweet_stats[day]['retweets']
			except KeyError:
				tempdict['retweets'] = 0 

			try:
				tempdict['favorites'] = handletweet_stats[day]['favorites']
			except KeyError:
				tempdict['favorites'] = 0 

			try:
				tempdict['tweets'] = handletweet_stats[day]['tweets']
			except KeyError:
				tempdict['tweets'] = 0 

			handle_stats.append(tempdict)
			# pp.pprint(tempdict)

		savetwittersummary(handle, handle_stats)

	db.close()




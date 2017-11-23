import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

from twitter import Twitter, OAuth, TwitterHTTPError, OAuth2, oauth2_dance
import pprint
pp = pprint.PrettyPrinter(indent=4)
import time
from time import sleep
import datetime
from datetime import timedelta
from email.utils import parsedate_tz, mktime_tz
from tracker.models import Handle, TwitterAccessToken, Geo

from django.db import IntegrityError
import MySQLdb
import MySQLdb.cursors
import random
import requests
import gc
from tracker.mysql_helper import safe_insert, safe_update
import json

todaydate = datetime.datetime.today()
todaydate = datetime.date(todaydate.year,todaydate.month,todaydate.day)
last_month_date = todaydate - timedelta(days = 30)
last_week_date = todaydate - timedelta(days = 7)
last_day_date = todaydate - timedelta(days = 1)
format = "%Y-%m-%d %H:%M:%S"

dbs = MySQLdb.connect(host='localhost',user='theseus',passwd='theseus123',db='theseus_social',charset='utf8')

class TwitterFollowers:
	def __init__(self):
		self.handle = Handle.objects.get(id = 1)
		self.geo = Geo.objects.get(id = 1)
		self.twitterapps = TwitterAccessToken.objects.filter(active = 1).order_by('id')[:6]
		self.appindex = 0

	def handle_twitter(self):
		self.getFollowers()
		dbs.close()

	def connect_to_api(self):
		if len(self.twitterapps)>0:
			if self.appindex == len(self.twitterapps)-1:
				self.appindex = 0
			# self.appindex = random.randint(0,len(self.twitterapps)-1)
			self.twapp = self.twitterapps[self.appindex]
			current_token = self.twitterapps[self.appindex]
			_TwitterOAuthToken = current_token.access_token
			_TwitterOAuthTokenSecret = current_token.access_token_secret
			_TwitterConsumerKey = current_token.api_key
			_TwitterConsumerSecret = current_token.api_secret

			TWITTER_ACCESS_DETAILS = (_TwitterConsumerKey, _TwitterConsumerSecret)
			twitterapi = Twitter(auth=OAuth2(bearer_token=oauth2_dance(*TWITTER_ACCESS_DETAILS)))
			# limit_status = twitterapi.application.rate_limit_status(resources="statuses,users")
			# pp.pprint(limit_status)
			# pp.pprint(TWITTER_ACCESS_DETAILS)
			self.appindex += 1
			return twitterapi
		else:
			print "No Twitter Apps"
			return False

	def raise_apierror(self, err):
		try:
			err = vars(err)
			print err["response_data"]
			errormsg = json.dumps(err["response_data"]["errors"])
		except KeyError:
			errormsg = "HTTP ERROR"
		message = "%s: %s"%(datetime.datetime.now(), errormsg)
		self.twapp.usage_stats = message
		self.twapp.save()
		print message

	def getFollowers(self):
		twitterapi = self.connect_to_api()
		try:
			print "HANDLE ==> %s %s Date ==> %s"%(self.handle.id, self.handle.name, todaydate)
			followers = twitterapi.followers.list(screen_name = self.handle.name, count = 100)
		except TwitterHTTPError as e:
			self.raise_apierror(e)
			return False
		newfollowers = 0
		updatedfollowers = 0
		followers['users'].reverse()
		for user_obj in followers['users']:
			utc_offset = self.checkifnull(user_obj.get('utc_offset', 0))
			time_zone = self.checkifnull(user_obj.get('time_zone', 0))
			userdetails = {
					'handle_id':self.handle.id,
					'user_id': user_obj.get('id_str'),
					'name': user_obj.get('name').encode('unicode_escape'),
					'screen_name': user_obj.get('screen_name').encode('unicode_escape'),
					'created_at': self.parse_date_str(user_obj['created_at']).strftime(format),
					'tweets': user_obj.get('statuses_count', 0),
					'description': user_obj.get('description', '').encode('unicode_escape'),
					'followers': user_obj.get('followers_count', 0),
					'favorites': user_obj.get('favourites_count', 0),
					'listed': user_obj.get('listed_count', 0),
					'friends': user_obj.get('friends_count', 0),
					'profile_image_url': user_obj.get('profile_image_url', ''),
					'utc_offset': utc_offset,
					'time_zone': time_zone,
					'location': user_obj.get('location', '').encode('unicode_escape'),
					'verified': user_obj.get('verified', False),
					'lang': user_obj.get('lang', 'en'),
					'insertdate': todaydate
				}
			cursor = dbs.cursor()
			try:
				user_query,user_data = safe_insert("tracker_twitterfollowers",userdetails)
				cursor.execute(user_query, user_data)
				newfollowers += 1
				# print 'Saved Follower: %s for Date: %s'%(userdetails['user_id'], userdetails['insertdate'])
			except MySQLdb.IntegrityError:
				uniquecolumns = ["user_id","insertdate"]
				user_query,user_data = safe_update("tracker_twitterfollowers",uniquecolumns,userdetails)
				cursor.execute(user_query, user_data)
				updatedfollowers += 1
				# print 'Updated Follower: %s for Date: %s'%(userdetails['user_id'], userdetails['insertdate'])
			except Exception as e:
				print e
				cursor.close()
				return False
			dbs.commit()
			cursor.close()
		print "New Followers: %s"%(newfollowers)
		print "Updated Followers: %s"%(updatedfollowers)

	def checkifnull(self, value):
		if value is None:
			return 0
		return value

	def parse_timezone(self, tweet):
		tzone = tweet['user'].get('time_zone', 0)
		if tzone == '' or tzone == None:
		    tzone = ''

		return tzone
    
	def parse_utc(self, tweet):
		utc = tweet['user'].get('utc_offset', 0)
		if utc == '' or utc == None:
		    utc = 0

		return utc

	def parse_date_str(self, date_string):
		return datetime.datetime.fromtimestamp(mktime_tz(parsedate_tz(date_string)))

if __name__ == '__main__':
	starttime = datetime.datetime.now()
	tf = TwitterFollowers()
	tf.handle_twitter()
	endtime = datetime.datetime.now() - starttime
	print "Completed in {0} secs.".format(endtime.seconds)
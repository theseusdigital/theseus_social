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
from tracker.models import Keyword, Handle, TwitterAccessToken, TwitterUser, HandleTweet, Geo, Hashtag

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

class TwitterHashtags:
	def __init__(self):
		self.keywords = Keyword.objects.filter(active = 1, platform__in = [2])
		self.handles = Handle.objects.filter(platform_id = 2, status = 2).order_by('max_tweet_id')
		self.hashtags = [hashtag.name for hashtag in Hashtag.objects.filter(active = 1)]
		self.geo = Geo.objects.get(id = 1)
		self.twitterapps = TwitterAccessToken.objects.filter(active = 1).order_by('id')[6:]
		self.appindex = 0

	def handle_twitter(self, gobackdays = 2):
		self.since = todaydate - timedelta(days = gobackdays)
		self.handle_tweets()
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

	def handle_tweets(self):
		if len(self.handles)==0:
			print 'No Handles Found'
			return
		self.requests = 0
		handle_no = 1
		for handle in self.handles:
			twitterapi = self.connect_to_api()
			if not twitterapi:
				break
			print "Collecting Twitter stats for handle "+handle.name
			self.handle = handle
			self.getTweets = True
			self.totalTweets = 0
			page = 1
			maxid = 0
			handle_id = handle.uniqueid
			user = self.getUser(twitterapi)
			if not user:
				continue
			while self.getTweets:
				try:
					twitterapi = self.connect_to_api()
					print "HANDLE ==> %s %s"%(handle.id, handle.name)
					print 'Page ==> %s'%(page)
					self._parsed_tweets = []
					if maxid == 0 and self.totalTweets == 0:
						print 'Saving tweets for fresh handle ',self.handle.name
						tweets = twitterapi.statuses.user_timeline(user_id = handle_id,count = 200,include_rts = False,tweet_mode = "extended")
					else:
						if self.totalTweets != 0:
							page += 1
							print 'Continuing to next page for handle ',str(self.handle.pk),' page ',page
							tweets = twitterapi.statuses.user_timeline(user_id = handle_id,count = 200,include_rts = False,max_id = (maxid-1),tweet_mode = "extended")
						else:
							print "Resuming saving tweets from ",maxid
							tweets = twitterapi.statuses.user_timeline(user_id = handle_id,count = 200,include_rts = False,since_id = (maxid-1),tweet_mode = "extended")
					self.requests += 1
					self._parsed_tweets = self.parse_handle_tweets(tweets)
					if len(self._parsed_tweets) > 0:
						maxid = long(self._parsed_tweets[-1]['tweet_id'])
					self.totalTweets += len(self._parsed_tweets)
					self.save_handle_tweets()
					if len(self._parsed_tweets)==0:
						print 'No More Tweets Found for Handle %s'%(self.handle.name)
						self.getTweets = False
					if not self.getTweets:
						self.handle.max_tweet_id = maxid
						self.handle.save()
						print "sleep"
						# sleep(30)
				except TwitterHTTPError as e:
					self.getTweets = False
					self.raise_apierror(e)
			print "REQUESTS: %s"%(self.requests)
			print "HANDLE NO: %s"%(handle_no)
			handle_no += 1
			print "\n"
			sleep(3)

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

	def getUser(self, twitterapi):
		try:
			print "HANDLE ==> %s %s"%(self.handle.id, self.handle.name)
			user_obj = twitterapi.users.show(user_id = self.handle.uniqueid)
			self.requests += 1
		except TwitterHTTPError as e:
			self.raise_apierror(e)
			print "REQUESTS: %s"%(self.requests)
			return False
		# pp.pprint(user_obj)
		userdetails = {
				'user_id': user_obj.get('id_str'),
				'name': user_obj.get('name').encode('unicode_escape'),
				'screen_name': user_obj.get('screen_name').encode('unicode_escape'),
				'created_at': self.parse_date_str(user_obj['created_at']).strftime('%Y-%m-%d %H:%M:%S'),
				'statuses_count': user_obj.get('statuses_count', 0),
				'description': user_obj.get('description', '').encode('unicode_escape'),
				'followers_count': user_obj.get('followers_count', 0),
				'favorites_count': user_obj.get('favourites_count', 0),
				'listed_count': user_obj.get('listed_count', 0),
				'friends_count': user_obj.get('friends_count', 0),
				'profile_image_url': user_obj.get('profile_image_url', ''),
				'utc_offset': user_obj.get('utc_offset', 0),
				'time_zone': user_obj.get('time_zone', 0),
				'location': user_obj.get('location', '').encode('unicode_escape'),
				'verified': user_obj.get('verified', False),
				'lang': user_obj.get('lang', 'en'),
				'lastupdated': datetime.datetime.now()
			}
		cursor = dbs.cursor()
		try:
			user_query,user_data = safe_insert("tracker_twitteruser",userdetails)
			cursor.execute(user_query, user_data)
			# TwitterUser(**userdetails).save()
			print 'Saved Twitter User: %s'%(userdetails['user_id'])
		except MySQLdb.IntegrityError:
			uniquecolumns = ["user_id"]
			user_query,user_data = safe_update("tracker_twitteruser",uniquecolumns,userdetails)
			cursor.execute(user_query, user_data)
			# TwitterUser.objects.filter(user_id = userdetails['user_id']).update(**userdetails)
			print 'Updated Twitter User: %s'%(userdetails['user_id'])
		except Exception as e:
			print e
			print "REQUESTS: %s"%(self.requests)
			cursor.close()
			return False
		dbs.commit()
		cursor.close()
		return True

	def parse_handle_tweets(self, tweets):
		parsed_tweets = []
		for tweet in tweets:
			insertime = datetime.datetime.today()
			insertime = insertime.strftime(format)
			tweet_time_tuple = self.parse_date_str(tweet['created_at'])
			tweet_time_date = datetime.date(tweet_time_tuple.year,tweet_time_tuple.month,tweet_time_tuple.day)
			if tweet_time_date < self.since:
				print 'Tweets before %s Ignored'%(self.since)
				self.getTweets = False
				return parsed_tweets
			parsed_tweet = {}
			parsed_tweet['geo_id'] = 1
			parsed_tweet['handle_id'] = self.handle.id
			parsed_tweet['text'] = tweet['full_text'].encode('unicode_escape')
			parsed_tweet['tweet_id'] = tweet['id_str']
			parsed_tweet['created_at'] = tweet_time_tuple.strftime('%Y-%m-%d %H:%M:%S')
			parsed_tweet['insert_time'] = insertime
			parsed_tweet['retweet_count'] = tweet['retweet_count']
			parsed_tweet['retweeted'] = tweet['retweeted']
			parsed_tweet['in_reply_to_user_id'] = tweet['in_reply_to_user_id']
			parsed_tweet['in_reply_to_status_id'] = tweet['in_reply_to_status_id']
			parsed_tweet['favorite_count'] = tweet['favorite_count']
			parsed_tweet['favorited'] = tweet['favorited']
			parsed_tweet['lang'] = tweet['lang']
			entities = tweet.get('entities')
			parsed_tweet['entities_hashtags'] = ''
			parsed_tweet['add'] = False
			if len(entities['hashtags']) > 0:
				hcount = 0
				for h in entities['hashtags']:
					if h['text'].encode('unicode_escape').lower() in self.hashtags:
						hcount += 1
				if hcount > 0:
					parsed_tweet['add'] = True
				parsed_tweet['entities_hashtags'] = ','.join([h['text'].encode('unicode_escape')
				                                for h in entities['hashtags']])
			parsed_tweet['entities_urls'] = ''
			if len(entities['urls']) > 0:
			    parsed_tweet['entities_urls'] = ','.join([h['display_url'].encode('unicode_escape')
			                                    for h in entities['urls']])

			parsed_tweet['entities_user_mentions'] = ''
			if len(entities['user_mentions']) > 0:
			    parsed_tweet['entities_user_mentions'] = ','.join([h['screen_name'].encode('unicode_escape')
			                                for h in entities['user_mentions']])

			parsed_tweet['entities_media'] = ''
			if 'media' in entities:
				parsed_tweet['entities_media'] = entities['media'][0]['media_url']

			if parsed_tweet['in_reply_to_user_id'] is None:
			    parsed_tweet['in_reply_to_user_id'] = 0
			    
			if parsed_tweet['in_reply_to_status_id'] is None:
			    parsed_tweet['in_reply_to_status_id'] = 0

			parsed_tweet['user_id'] = tweet['user']['id_str']
			parsed_tweet['active'] = True
			parsed_tweets.append(parsed_tweet)
		return parsed_tweets

	def save_handle_tweets(self):
		savedtweets = []
		updatedtweets = []
		for tweet in self._parsed_tweets:
			if tweet['add']:
				del tweet['add']
				cursor = dbs.cursor()
				try:
					tweet_query,tweet_data = safe_insert("tracker_handletweet",tweet)
					cursor.execute(tweet_query, tweet_data)
					# HandleTweet(**tweet).save()
					savedtweets.append(tweet['tweet_id'])
				except MySQLdb.IntegrityError:
					uniquecolumns = ["tweet_id","handle_id"]
					tweet_query,tweet_data = safe_update("tracker_handletweet",uniquecolumns,tweet)
					cursor.execute(tweet_query, tweet_data)
					# HandleTweet.objects.filter(tweet_id=tweet['tweet_id'],handle_id=tweet['handle_id']).update(**tweet)
					updatedtweets.append(tweet['tweet_id'])
				except Exception as e:
					print e
					print "REQUESTS: %s"%(self.requests)
					cursor.close()
					continue
				dbs.commit()
				cursor.close()
		print "%s Tweets Saved"%(len(savedtweets))
		print "%s Tweets Updated"%(len(updatedtweets))
		# gc.collect()

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
	print sys.argv
	if(len(sys.argv)>1):
		gobackdays = int(sys.argv[1])
	else:
		gobackdays = 2
	ts = TwitterHashtags()
	ts.handle_twitter(gobackdays)
	endtime = datetime.datetime.now() - starttime
	print "Completed in {0} secs.".format(endtime.seconds)
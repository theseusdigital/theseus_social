import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

import datetime
from datetime import timedelta

import pprint
pp = pprint.PrettyPrinter(indent=4)

from urllib import urlencode,urlopen
import json

from twitter import Twitter, TwitterHTTPError, OAuth2, oauth2_dance

import apiclient
from apiclient.discovery import build
from apiclient.http import HttpMock

from tracker.models import TwitterAccessToken, FacebookAccessToken, GoogleAccessToken

def query_twitter():
	current_token = TwitterAccessToken.objects.get(id = 1, active = 1)

	_TwitterOAuthToken = current_token.access_token
	_TwitterOAuthTokenSecret = current_token.access_token_secret
	_TwitterConsumerKey = current_token.api_key
	_TwitterConsumerSecret = current_token.api_secret

	TWITTER_ACCESS_DETAILS = (_TwitterConsumerKey, _TwitterConsumerSecret)
	twitterapi = Twitter(auth=OAuth2(bearer_token=oauth2_dance(*TWITTER_ACCESS_DETAILS)))

	tweets = twitterapi.statuses.user_timeline(id = 348375714,count = 5,include_rts = True)

	for tweet in tweets:
		pp.pprint(tweet)

def query_facebook():
	sincedate = datetime.date(year=2017, month=7, day=29)
	since = sincedate.strftime('%Y-%m-%d')
	graphuserurl = "https://graph.facebook.com/%s/?fields=%s&access_token=%s"
	graphpostsurl = "https://graph.facebook.com/%s/feed/?since=%s&fields=%s&access_token=%s"
	fbapp = FacebookAccessToken.objects.get(id = 1,active = 1)
	current_token = fbapp.appid+'|'+fbapp.api_secret

	userfields = ['id','name','description','fan_count','talking_about_count','picture','is_verified']
	postfields = ['id','object_id','picture','from','message','created_time',
						'shares','type','status_type','link','comments.limit(1).summary(true)',
						'likes.limit(1).summary(true)']
	userfields_str = ','.join(userfields)
	postfields_str = ','.join(postfields)

	userurl = graphuserurl % (238044912896496, userfields_str, current_token)
	# response = urlopen(userurl)
	# userdata = json.loads(response.read())
	# pp.pprint(userdata)

	posturl = graphpostsurl % (238044912896496, since, postfields_str, current_token)
	response = urlopen(posturl)
	postdata = json.loads(response.read())
	pp.pprint(postdata)

def query_youtube(youtubeid=None, name=None):
	googleapp = GoogleAccessToken.objects.get(id = 1,active = 1)
	api_key = googleapp.api_key
	youtubeapi = build('youtube', 'v3', developerKey = api_key)
	params = {'part': 'id,snippet,statistics,contentDetails', 'maxResults': 50}
	youtubeid = "UCh0Ob3N4miyi773toqSYj-A"
	if youtubeid is not None:
	    params['id'] = youtubeid
	elif name is not None:
	    params['forUsername'] = name
	# try:
	# 	response = youtubeapi.channels().list(**params).execute()
	# except apiclient.errors.HttpError as err:
	# 	print err
	# 	return None

	# channel = None
	# for itm in response['items']:
	#     if itm['kind'] == 'youtube#channel':
	#         channel = itm
	#         break
	# pp.pprint(channel)

	params = {'part': 'snippet,statistics', 'maxResults': 50}
	ids = "6ZQejH6IX7s,4AgL4gDvzWE"
	if ids is not None:
	    params['id'] = ids
	else:
	    return None

	try:
	    response = youtubeapi.videos().list(**params).execute()
	    # pp.pprint(response['items'])
	except apiclient.errors.HttpError as err:
		print err
		return None

	for videoItem in response['items']:
		pp.pprint(videoItem)

# query_facebook()
query_twitter()
# query_youtube()
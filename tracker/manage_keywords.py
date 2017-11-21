import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

import facebook
import requests
import pprint
pp = pprint.PrettyPrinter(indent=4)
import random
from urllib import urlencode,urlopen
import json
from twitter import Twitter, OAuth, TwitterHTTPError, OAuth2, oauth2_dance
from apiclient.discovery import build

from tracker.models import Platform, Keyword, Handle, FacebookAccessToken, TwitterAccessToken, GoogleAccessToken, InstagramAccessToken

fbapps = FacebookAccessToken.objects.filter(active=1)
fbtokens = [fbapp.appid+'|'+fbapp.api_secret for fbapp in fbapps]

twapps = TwitterAccessToken.objects.filter(active=1)

googleapps = GoogleAccessToken.objects.filter(active = 1)

igapps = InstagramAccessToken.objects.filter(active = 1)

STATUS = 1

def getFacebookHandles(keyword, handle_id = None):
	handle_query = keyword.name.split(":")[-1]
	current_token = fbtokens[random.randint(0,len(fbtokens)-1)]
	# graph = facebook.GraphAPI(access_token=current_token, version='2.7')
	apiurl =  "https://graph.facebook.com/%s?access_token=%s&fields=id,name,username"
	apiurl = apiurl % (handle_query,current_token)
	print "FBURL=> "+apiurl
	response = urlopen(apiurl)
	data = json.loads(response.read())
	if data.get('error'):
		print 'No Facebook Handles Found for keyword '+keyword.name
		pp.pprint(data)
		return False
	else:
		pp.pprint(data)
		if data.get("username"):
			handlename = data['username']
		else: 
			handlename = data['name']
		handledetails = {}
		handledetails['name'] = handlename
		handledetails['uniqueid'] = data['id']
		handledetails['platform_id'] = 1
		handledetails['keyword_id'] = keyword.id
		handledetails['status'] = STATUS
		if handle_id:
			handledetails['id'] = handle_id

		handle = Handle(**handledetails)
		handle.save()
		pp.pprint(handledetails)
		print 'Facebook Handle Saved'
		return True

def getTwitterHandles(keyword, handle_id = None):
	handle_query = keyword.name.split(":")[-1]
	current_token = twapps[random.randint(0,len(twapps)-1)]
	_TwitterOAuthToken = current_token.access_token
	_TwitterOAuthTokenSecret = current_token.access_token_secret
	_TwitterConsumerKey = current_token.api_key
	_TwitterConsumerSecret = current_token.api_secret

	TWITTER_ACCESS_DETAILS = (_TwitterOAuthToken, _TwitterOAuthTokenSecret,
		       _TwitterConsumerKey, _TwitterConsumerSecret)

	twtr = Twitter(auth=OAuth(*TWITTER_ACCESS_DETAILS))
	try:
		userdetails = twtr.users.show(id = handle_query)
	except TwitterHTTPError as e:
		print 'No Twitter Handles Found for keyword '+keyword.name
		print e
		return False
	# pp.pprint(userdetails)
	handledetails = {}
	handledetails['uniqueid'] = userdetails['id_str']
	handledetails['name'] = userdetails['screen_name']
	handledetails['platform_id'] = 2
	handledetails['keyword_id'] = keyword.id
	handledetails['status'] = STATUS
	if handle_id:
		handledetails['id'] = handle_id

	handle = Handle(**handledetails)
	handle.save()
	pp.pprint(handledetails)
	print 'Twitter Handle Saved'
	return True

def getYoutubeHandles(keyword, handle_id = None):
	current_token = googleapps[random.randint(0,len(googleapps)-1)]
	api_key = current_token.api_key
	youtube = build('youtube', 'v3', developerKey=api_key)
	keywordset = keyword.name.split(":")
	handle_prefix = keywordset[0]
	handle_query = keywordset[-1]
	params = {'part': 'statistics'}
	if len(keywordset) == 2:
	    params['id'] = handle_query
	    handlename = handle_prefix
	else:
	    params['forUsername'] = handle_query
	    handlename = keyword.name
	response = youtube.channels().list(**params).execute()
	# pp.pprint(response)
	channel = None
	for itm in response['items']:
	    if itm['kind'] == 'youtube#channel':
	        channel = itm
	        break
	if channel is not None:
		pp.pprint(channel)
		handledetails = {}
		handledetails['uniqueid'] = channel['id']
		handledetails['name'] = handlename
		handledetails['platform_id'] = 3
		handledetails['keyword_id'] = keyword.id
		handledetails['status'] = STATUS
		if handle_id:
			handledetails['id'] = handle_id

		handle = Handle(**handledetails)
		handle.save()
		pp.pprint(handledetails)
		print 'Youtube Handle Saved'
		return True
	else:
		print 'No Youtube Handles Found for keyword '+keyword.name
		pp.pprint(response)
		return False

def getInstagramHandles(keyword, handle_id = None):
	handle_query = keyword.name.split(":")[-1]
	current_token = igapps[random.randint(0,len(igapps)-1)]
	# graph = facebook.GraphAPI(access_token=current_token, version='2.7')
	apiurl =  "https://api.instagram.com/v1/users/search?q=%s&access_token=%s&count=1"
	apiurl = apiurl % (handle_query,current_token.access_token)
	print "IGURL=> "+apiurl
	response = urlopen(apiurl)
	data = json.loads(response.read())
	if data.get('data'):
		igdata = data['data']
		if len(igdata)>0:
			igdata = igdata[0]
			pp.pprint(igdata)
			if igdata.get("username"):
				handlename = igdata['username']
			else: 
				handlename = keyword.name
			handledetails = {}
			handledetails['name'] = handlename
			handledetails['uniqueid'] = igdata['id']
			handledetails['platform_id'] = 4
			handledetails['keyword_id'] = keyword.id
			handledetails['status'] = STATUS
			if handle_id:
				handledetails['id'] = handle_id

			handle = Handle(**handledetails)
			handle.save()
			pp.pprint(handledetails)
			print 'Instagram Handle Saved'
			return True
	print 'No Instagram Handles Found for keyword '+keyword.name
	pp.pprint(data)
	return False

if __name__ == '__main__':
	callables = {
		1:getFacebookHandles,
		2:getTwitterHandles,
		3:getYoutubeHandles,
		4:getInstagramHandles
		}
	platforms = Platform.objects.filter(active = True).order_by("id")
	for keyword in Keyword.objects.filter(active = True):
		for platform in platforms:
			handles = Handle.objects.filter(platform_id = platform.id, keyword_id = keyword.id, status__in = [1,2])
			if len(handles) == 0:
				if keyword.platform.filter(id = platform.id).exists():
					print "Searching handle for KEYWORD %s on PLATFORM %s"%(keyword.name,platform.name)
					result = callables[platform.id](keyword)
					if not result:
						keyword.platform.remove(platform)
						print "KEYWORD %s inactive on PLATFORM %s"%(keyword.name,platform.name)
			else:
				for handle in handles.filter(uniqueid = ""):
					print "Updating HANDLE %s for keyword %s on PLATFORM %s"%(handle.name,keyword.name,platform.name)
					result = callables[platform.id](keyword,handle.id)
			

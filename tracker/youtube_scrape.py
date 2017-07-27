import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

import apiclient
from apiclient.discovery import build
from apiclient.http import HttpMock
import pprint
pp = pprint.PrettyPrinter(indent=4)
import time
from time import sleep
import datetime
from datetime import timedelta
from tracker.models import Handle, Keyword, YoutubeChannel, YoutubeChannelVideo, GoogleAccessToken

import MySQLdb
import MySQLdb.cursors
from django.db import IntegrityError
import random
import json
import gc
from tracker.mysql_helper import safe_insert, safe_update

todaydate = datetime.datetime.today()
todaydate = datetime.date(todaydate.year,todaydate.month,todaydate.day)

dbs = MySQLdb.connect(host='localhost',user='theseus',passwd='theseus123',db='theseus_social',charset='utf8')

class YoutubeScraper:
	def __init__(self, gobackdays = 7):
		self.googleapps = GoogleAccessToken.objects.filter(active = 1)
		self.sincedate = todaydate - datetime.timedelta(days = gobackdays)
		# self.handle_youtube()

	def handle_youtube(self):
		self.handle_videos()
		dbs.close()

	def get_apikey(self):
		appindex = random.randint(0,len(self.googleapps)-1)
		self.ytapp = self.googleapps[appindex]
		return self.ytapp.api_key

	def handle_videos(self):
		ythandles = Handle.objects.filter(platform_id = 3, status = 1)
		handle_no = 1
		for handle in ythandles:
			api_key = self.get_apikey()
			self.youtube = build('youtube', 'v3', developerKey = api_key)
			self.handle = handle
			print "HANDLE ==> %s"%(handle.name)
			youtubeid = handle.uniqueid
			chdetails = self.getChannel(id=youtubeid)
			if chdetails:
				chdetails['handle_id'] = handle.pk
				playlistid = chdetails['playlist']
				# pp.pprint(chdetails)
				cursor = dbs.cursor()
				try:
					channel_query,channel_data = safe_insert("tracker_youtubechannel",chdetails)
					cursor.execute(channel_query, channel_data)
					# YoutubeChannel(**chdetails).save()
					print 'Saved Youtube Channel: %s'%(chdetails['youtubeid'])
				except MySQLdb.IntegrityError:
					uniquecolumns = ["youtubeid"]
					channel_query,channel_data = safe_update("tracker_youtubechannel",uniquecolumns,chdetails)
					cursor.execute(channel_query, channel_data)
					# YoutubeChannel.objects.filter(youtubeid = chdetails['youtubeid']).update(**chdetails)
					print 'Updated Youtube Channel: %s'%(chdetails['youtubeid'])
				except Exception as e:
					print e
					cursor.close()
					continue
				dbs.commit()
				cursor.close()

				self.nextToken = None
				self.page = 1
				self.getPlaylist(playlistid = playlistid, since = self.sincedate)
			print "HANDLE NO: %s"%(handle_no)
			handle_no += 1
			print "sleep\n"
			sleep(3)

	def getSharedFB(self, id):
	    accessTokenlist = ['879619345514435|14b8765e98756ffe65102a0c6d181f1e']
	    apiurl = "https://graph.facebook.com/?id=https://www.youtube.com/watch?v=##VIDEOID&access_token=##AT"
	    apiurl = apiurl.replace('##VIDEOID',id)
	    apiurl = apiurl.replace('##AT',accessTokenlist[random.randint(0,len(accessTokenlist)-1)])
	    print apiurl
	    response = urlopen(apiurl)
	    data = json.loads(response.read())

	    try:
	        sharedonfb = data['shares']
	    except:
	        sharedonfb = 0

	    print sharedonfb
	    return sharedonfb

	def raise_apierror(self, err):
		error = vars(err)
		try:
			content = json.loads(error["content"])
			message = content["error"]["message"]
		except KeyError:
			message = "HTTP ERROR"
		message = "%s: %s"%(datetime.datetime.now(), message)
		self.ytapp.usage_stats = message
		self.ytapp.save()
		print message

	def getVideoStats(self, ids):
		params = {'part': 'statistics', 'maxResults': 50}

		if ids is not None:
		    params['id'] = ids
		else:
		    return None

		try:
		    response = self.youtube.videos().list(**params).execute()
		    # pp.pprint(response['items'])
		except apiclient.errors.HttpError as err:
			self.raise_apierror(err)
			return None

		for videoItem in response['items']:
			videostats = {
				'youtubeid':videoItem['id'],
				'comments':videoItem['statistics']['commentCount'],
				'likes':videoItem['statistics']['likeCount'],
				'views':videoItem['statistics']['viewCount'],
				'dislikes':videoItem['statistics']['dislikeCount'],
				'favorites':videoItem['statistics']['favoriteCount']
			}
			cursor = dbs.cursor()
			try:
				uniquecolumns = ["youtubeid"]
				video_query,video_data = safe_update("tracker_youtubechannelvideo",uniquecolumns,videostats)
				cursor.execute(video_query, video_data)
				# YoutubeChannelVideo.objects.filter(youtubeid=videoItem['id']).update(**videostats)
			except Exception as e:
				print e
				cursor.close()
				continue
			dbs.commit()
			cursor.close()
			# sharedonfb = self.getSharedFB(id)
		print 'Updated Stats for %s Videos'%(len(response['items']))

	def getPlaylist(self, playlistid, since):
		print 'HANDLE ==> %s %s'%(self.handle.id, self.handle.name)
		print 'Page ==> %s'%(self.page)
		params = {'part': 'snippet,contentDetails', 'maxResults': 50}
		if self.nextToken:
			params['pageToken'] = self.nextToken

		if playlistid is not None:
		    params['playlistId'] = playlistid
		else:
		    return
		try:
			response = self.youtube.playlistItems().list(**params).execute()
		except apiclient.errors.HttpError as err:
			self.raise_apierror(err)
			return
		# pp.pprint(response['items'][0])
		self.nextToken = response.get('nextPageToken', None)

		if len(response['items']) == 0:
		    return
		else:
			pass

		videos = []
		for itm in response['items']:
			# pp.pprint(itm)
			vid = {}
			vid['published'] = self.convertYDateTime(itm['snippet']['publishedAt'])
			if vid['published'].date() < since:
				self.nextToken = None
				print 'Videos before %s Ignored'%(since)
				break
			vid['etag'] = itm['etag']
			vid['youtubeid'] = itm['contentDetails']['videoId']
			vid['title'] = itm['snippet']['title'].encode('unicode_escape')
			vid['description'] = itm['snippet']['description'].encode('unicode_escape')[:255]
			videos.append(vid)

		print "%s Videos Found"%(len(videos))
		self.saveVideos(videos)
		videoids = ','.join([vid['youtubeid'] for vid in videos])
		self.getVideoStats(ids = videoids)
		if self.nextToken:
			self.page += 1
			self.getPlaylist(playlistid = playlistid, since = self.sincedate)

	def saveVideos(self, videos):
		savedvideos = []
		updatedvideos = []
		defaults = {}
		defaults['comments'] = 0
		defaults['likes'] = 0
		defaults['views'] = 0
		defaults['dislikes'] = 0
		defaults['favorites'] = 0
		defaults['sharedonfb'] = 0

		for video in videos:
			video['handle_id'] = self.handle.id
			newvideo = dict(video.items() + defaults.items())
			cursor = dbs.cursor()
			try:
				video_query,video_data = safe_insert("tracker_youtubechannelvideo",newvideo)
				cursor.execute(video_query, video_data)
				# YoutubeChannelVideo(**newvideo).save()
				savedvideos.append(newvideo['youtubeid'])
			except MySQLdb.IntegrityError:
				uniquecolumns = ["youtubeid"]
				video_query,video_data = safe_update("tracker_youtubechannelvideo",uniquecolumns,video)
				cursor.execute(video_query, video_data)
				# YoutubeChannelVideo.objects.filter(youtubeid = video['youtubeid']).update(**video)
				updatedvideos.append(video['youtubeid'])
			except Exception as e:
				print e,"for youtubeid: "+video['youtubeid']
				cursor.close()
				continue
			dbs.commit()
			cursor.close()
		print "%s Videos Saved"%(len(savedvideos))
		print "%s Videos Updated"%(len(updatedvideos))

	def getChannel(self, id=None, name=None):
		params = {'part': 'id,snippet,statistics,contentDetails', 'maxResults': 50}
		if id is not None:
		    params['id'] = id
		elif name is not None:
		    params['forUsername'] = name
		try:
			response = self.youtube.channels().list(**params).execute()
		except apiclient.errors.HttpError as err:
			self.raise_apierror(err)
			return None
		# pp.pprint(response)
		channel = None
		for itm in response['items']:
		    if itm['kind'] == 'youtube#channel':
		        channel = itm
		        break

		if channel is not None:
		    published_dt = self.convertYDateTime(channel['snippet']['publishedAt'])
		    channel_data = {}
		    channel_data['youtubeid'] = channel['id']
		    channel_data['etag'] = channel['etag']
		    channel_data['title'] = channel['snippet']['title'].encode('unicode_escape')
		    channel_data['description'] = channel['snippet']['description'].encode('unicode_escape')
		    channel_data['playlist'] = channel['contentDetails']['relatedPlaylists']['uploads']
		    channel_data['published'] = published_dt
		    channel_data['comments'] = channel['statistics']['commentCount']
		    channel_data['subscribers'] = channel['statistics']['subscriberCount']
		    channel_data['videos'] = channel['statistics']['videoCount']
		    channel_data['views'] = channel['statistics']['viewCount']  
		    return channel_data
		return None

	def convertYDateTime(self, ydate):
		return datetime.datetime(*time.strptime(ydate,
		                                       '%Y-%m-%dT%H:%M:%S.000Z')[0:6])

if __name__ == '__main__':
	starttime = datetime.datetime.now()
	print sys.argv
	if(len(sys.argv)>1):
		gobackdays = int(sys.argv[1])
	else:
		gobackdays = 7
	ys = YoutubeScraper(gobackdays)
	ys.handle_youtube()
	endtime = datetime.datetime.now() - starttime
	print "Completed in {0} secs.".format(endtime.seconds)
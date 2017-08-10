import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

import pprint
pp = pprint.PrettyPrinter(indent=4)
import time
from time import sleep
import datetime
from datetime import timedelta
from tracker.models import Handle, FacebookUser, FacebookDailyNums, \
							TwitterUser, TwitterDailyNums, YoutubeChannel, \
							YoutubeDailyNums, InstagramUser, InstagramDailyNums
from django.db import IntegrityError

import random
import gc

todaydate = datetime.datetime.today().date()

class HandleDailyNumbers:
	def __init__(self):
		pass

	def get_dailynums(self):
		self.handle_facebook()
		self.handle_twitter()
		self.handle_youtube()
		self.handle_instagram()
		
	def handle_facebook(self):
		print "\nFACEBOOK"
		print "TODAY: %s"%(todaydate)
		fbhandles = Handle.objects.filter(platform_id = 1, status = 1)
		for handle in fbhandles:
			try:
				fbuser = FacebookUser.objects.get(uniqueid = handle.uniqueid)
				todaynums = {}
				todaynums["likes"] = fbuser.likes
				todaynums["talkingabout"] = fbuser.talkingabout
				todaynums["addedtime"] = todaydate
				todaynums["handle_id"] = handle.id
			except FacebookUser.DoesNotExist:
				print "User Not Found for HANDLE %s"%(handle.name)
				continue
			try:
				FacebookDailyNums(**todaynums).save()
				print "FacebookDailyNums for HANDLE %s %s Saved"%(handle.id, handle.name)
			except IntegrityError:
				FacebookDailyNums.objects.filter(handle_id = handle.id, addedtime = todaydate).update(**todaynums)
				print "FacebookDailyNums for HANDLE %s %s Updated"%(handle.id, handle.name)
			except Exception as e:
				print e
				
	def handle_twitter(self):
		print "\nTWITTER"
		print "TODAY: %s"%(todaydate)
		twhandles = Handle.objects.filter(platform_id = 2, status = 1)
		for handle in twhandles:
			try:
				twuser = TwitterUser.objects.get(user_id = handle.uniqueid)
				todaynums = {}
				todaynums["tweets"] = twuser.statuses_count
				todaynums["followers"] = twuser.followers_count
				todaynums["favorites"] = twuser.favorites_count
				todaynums["following"] = twuser.friends_count
				todaynums["addedtime"] = todaydate
				todaynums["handle_id"] = handle.id
			except TwitterUser.DoesNotExist:
				print "User Not Found for HANDLE %s"%(handle.name)
				continue
			try:
				TwitterDailyNums(**todaynums).save()
				print "TwitterDailyNums for HANDLE %s %s Saved"%(handle.id, handle.name)
			except IntegrityError:
				TwitterDailyNums.objects.filter(handle_id = handle.id, addedtime = todaydate).update(**todaynums)
				print "TwitterDailyNums for HANDLE %s %s Updated"%(handle.id, handle.name)
			except Exception as e:
				print e

	def handle_youtube(self):
		print "\nYOUTUBE"
		print "TODAY: %s"%(todaydate)
		ythandles = Handle.objects.filter(platform_id = 3, status = 1)
		for handle in ythandles:
			try:
				ytuser = YoutubeChannel.objects.get(handle_id = handle.id)
				todaynums = {}
				todaynums["videos"] = ytuser.videos
				todaynums["views"] = ytuser.views
				todaynums["subscribers"] = ytuser.subscribers
				todaynums["comments"] = ytuser.comments
				todaynums["addedtime"] = todaydate
				todaynums["handle_id"] = handle.id
			except YoutubeChannel.DoesNotExist:
				print "Channel Not Found for HANDLE %s"%(handle.name)
				continue
			try:
				YoutubeDailyNums(**todaynums).save()
				print "YoutubeDailyNums for HANDLE %s %s Saved"%(handle.id, handle.name)
			except IntegrityError:
				YoutubeDailyNums.objects.filter(handle_id = handle.id, addedtime = todaydate).update(**todaynums)
				print "YoutubeDailyNums for HANDLE %s %s Updated"%(handle.id, handle.name)
			except Exception as e:
				print e

	def handle_instagram(self):
		print "\nINSTAGRAM"
		print "TODAY: %s"%(todaydate)
		ighandles = Handle.objects.filter(platform_id = 4, status = 1)
		for handle in ighandles:
			try:
				iguser = InstagramUser.objects.get(uniqueid = handle.uniqueid)
				todaynums = {}
				todaynums["posts"] = iguser.posts
				todaynums["friends"] = iguser.friends
				todaynums["followers"] = iguser.followers
				todaynums["addedtime"] = todaydate
				todaynums["handle_id"] = handle.id
			except InstagramUser.DoesNotExist:
				print "User Not Found for HANDLE %s"%(handle.name)
				continue
			try:
				InstagramDailyNums(**todaynums).save()
				print "InstagramDailyNums for HANDLE %s %s Saved"%(handle.id, handle.name)
			except IntegrityError:
				InstagramDailyNums.objects.filter(handle_id = handle.id, addedtime = todaydate).update(**todaynums)
				print "InstagramDailyNums for HANDLE %s %s Updated"%(handle.id, handle.name)
			except Exception as e:
				print e

if __name__ == '__main__':
	hdn = HandleDailyNumbers()
	hdn.get_dailynums()
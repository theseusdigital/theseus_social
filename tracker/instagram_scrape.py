import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

import facebook
import pprint
pp = pprint.PrettyPrinter(indent=4)
import time
from time import sleep
import datetime
from datetime import timedelta
from tracker.models import Handle, InstagramAccessToken, InstagramHandlePost, InstagramUser

from django.db import IntegrityError
import MySQLdb
import MySQLdb.cursors
import random
import requests
import gc
from urllib import urlencode,urlopen
import json
from tracker.mysql_helper import safe_insert, safe_update

todaydate = datetime.datetime.today()
todaydate = datetime.date(todaydate.year,todaydate.month,todaydate.day)

dbs = MySQLdb.connect(host='localhost',user='tracker',passwd='tracker123',db='theseus_social',charset='utf8')

class InstagramScraper:
	def __init__(self, gobackdays = 7):
		self._india_offset = timedelta(hours = 5,minutes = 30)
		sincedate = todaydate - datetime.timedelta(days = gobackdays)
		self.since = sincedate.strftime('%Y-%m-%d')

	def handle_instagram(self):
		self.handle_posts()
		dbs.close()

	def handle_posts(self):
		iguserurl = "https://api.instagram.com/v1/users/%s/?access_token=%s"
		igpostsurl = "https://api.instagram.com/v1/users/%s/media/recent/?access_token=%s"
		igapps = InstagramAccessToken.objects.filter(active = 1)
		ighandles = Handle.objects.filter(platform_id = 4, status__in = [1,2])
		handle_no = 1
		for handle in ighandles:
			if handle.status == 2:
				self.getBotUser(handle)
			else:
				self.page = 0
				self.igapp = igapps[random.randint(0,len(igapps)-1)]
				current_token = self.igapp.access_token
				# self.graph = facebook.GraphAPI(access_token=current_token, version='2.7')
				userurl = iguserurl % (handle.uniqueid, current_token)
				response = urlopen(userurl)
				userdata = json.loads(response.read())
				if not userdata.get("data"):
					print 'API URL==>\n%s'%(userurl)
					self.raise_apierror(userdata)
					continue
				user = self.getUser(handle,userdata,userurl)
				if not user:
					continue

				posturl = igpostsurl % (handle.uniqueid, current_token)
				response = urlopen(posturl)
				postdata = json.loads(response.read())
				if not postdata.get("data"):
					print 'API URL==>\n%s'%(posturl)
					self.raise_apierror(postdata)
					continue

				self.getPosts(handle,postdata,posturl)
			print "HANDLE NO: %s"%(handle_no)
			handle_no += 1
			print "sleep\n"
			sleep(3)

	def raise_apierror(self, err):
		pp.pprint(err)
		errormsg = err.get("error_message","HTTP ERROR")
		message = "%s: %s"%(datetime.datetime.now(), errormsg)
		self.igapp.usage_stats = message
		self.igapp.save()
		print message

	def getBotUser(self, handle):
		print "HANDLE ==> %s %s"%(handle.id, handle.name)
		handle_query = handle.name
		igurl =  "https://www.instagram.com/%s/?__a=1"
		igurl = igurl % (handle_query)
		print 'API URL==>\n%s'%(igurl)
		response = urlopen(igurl)
		data = json.loads(response.read())
		if data.get('user'):
			userdata = data['user']
			userdetails = {}
			userdetails['uniqueid'] = userdata['id']
			userdetails['name'] = userdata['full_name'].encode('unicode_escape')
			userdetails['description'] = userdata.get("biography","")[:500].encode('unicode_escape')
			userdetails['posts'] = userdata['media']['count']
			userdetails['friends'] = userdata['follows']['count']
			userdetails['followers'] = userdata['followed_by']['count']
			try:
				userdetails['picture'] = userdata['profile_pic_url']
			except KeyError:
				userdetails['picture'] = ""
		else:
			print "User Data Not Found"
			return False

		cursor = dbs.cursor()
		try:
			user_query,user_data = safe_insert("tracker_instagramuser",userdetails)
			cursor.execute(user_query, user_data)
			# FacebookUser(**userdetails).save()
			print 'Saved Instagram User: %s'%(userdetails['uniqueid'])
		except MySQLdb.IntegrityError:
			uniquecolumns = ["uniqueid"]
			user_query,user_data = safe_update("tracker_instagramuser",uniquecolumns,userdetails)
			cursor.execute(user_query, user_data)
			# FacebookUser.objects.filter(uniqueid=userdetails['uniqueid']).update(**userdetails)
			print 'Updated Instagram User: %s'%(userdetails['uniqueid'])
		except Exception as e:
			print e
			cursor.close()
			return False
		dbs.commit()
		cursor.close()
		return False

	def getUser(self, handle, data, apiurl='firsturl'):
		print "HANDLE ==> %s %s"%(handle.id, handle.name)
		print 'API URL==>\n%s'%(apiurl)
		userdata = data['data']
		if userdata.get("id"):
			userdetails = {}
			userdetails['uniqueid'] = userdata['id']
			userdetails['name'] = userdata['full_name'].encode('unicode_escape')
			userdetails['description'] = userdata.get("bio","")[:500].encode('unicode_escape')
			userdetails['posts'] = userdata['counts']['media']
			userdetails['friends'] = userdata['counts']['follows']
			userdetails['followers'] = userdata['counts']['followed_by']
			try:
				userdetails['picture'] = userdata['profile_picture']
			except KeyError:
				userdetails['picture'] = ""
			# pp.pprint(userdetails)
		else:
			print "User Data Not Found"
			return False
		cursor = dbs.cursor()
		try:
			user_query,user_data = safe_insert("tracker_instagramuser",userdetails)
			cursor.execute(user_query, user_data)
			# FacebookUser(**userdetails).save()
			print 'Saved Instagram User: %s'%(userdetails['uniqueid'])
		except MySQLdb.IntegrityError:
			uniquecolumns = ["uniqueid"]
			user_query,user_data = safe_update("tracker_instagramuser",uniquecolumns,userdetails)
			cursor.execute(user_query, user_data)
			# FacebookUser.objects.filter(uniqueid=userdetails['uniqueid']).update(**userdetails)
			print 'Updated Instagram User: %s'%(userdetails['uniqueid'])
		except Exception as e:
			print e
			cursor.close()
			return False
		dbs.commit()
		cursor.close()
		return True
			
	def getPosts(self, handle, data, apiurl='firsturl'):
		sleep(3)
		print "HANDLE ==> %s %s"%(handle.id, handle.name)
		print 'API URL==>\n%s'%(apiurl)
		try:
			firstpage = data['data']
		except:
			print " Data blank check URL-->"+apiurl+"\nResponse is below::"
		try:	
			print "%s Posts Found"%(len(firstpage))
			self.savePosts(handle,firstpage)
			# next = requests.get(data['paging']['next']).json()
			# apiurl = data['paging']['next']
			# self.page += 1
			# print 'Next Page: %s'%(self.page)
			# self.getPosts(handle,next,apiurl)
		except:
			print "Posts Retrieved Since %s"%(self.since)
			print "HANDLE %s: Next not found, %s Pages Found"%(handle.name,self.page)


	def savePosts(self, handle, postslist):
		savedposts = []
		updatedposts = []
		for p in postslist:
			posts = {}
			
			posts['handle_id'] = handle.id
			posts['likes'] = 0
			posts['comments'] = 0
			posts['likes'] = p['likes']['count']
			posts['comments'] = p['comments']['count']

			posts['postid'] = p.get('id').split('_')[0]
			
			if p.get('caption'):
				posts['caption'] = p['caption']['text']
			else:
				posts['caption'] = ""
			posts['caption'] = posts['caption'].encode('unicode_escape')[:255]

			posts['tags'] = ",".join([tag.encode('unicode_escape') for tag in p['tags']])

			posts['author'] = p.get('user').get('id')	
			posts['url'] = p['link']
			posts['postimg'] = p['images']['thumbnail']['url']
			
			raw_published = p.get('created_time')

			dt_published = datetime.datetime.fromtimestamp(long(raw_published))
			# indiatz_published = dt_published+self._india_offset
			posts['published'] = dt_published
			posts['published_date'] = dt_published.strftime('%Y-%m-%d')
			posts['lastupdated'] = datetime.datetime.now()
			posts['posttype'] = p.get('type')
			posts['views'] = 0
			posts['active'] = True
			# pp.pprint(posts)
			cursor = dbs.cursor()
			try:
				post_query,post_data = safe_insert("tracker_instagramhandlepost",posts)
				cursor.execute(post_query, post_data)		
				savedposts.append(posts['postid'])
			except MySQLdb.IntegrityError:
				del posts['views']
				uniquecolumns = ["handle_id","postid"]
				post_query,post_data = safe_update("tracker_instagramhandlepost",uniquecolumns,posts)
				cursor.execute(post_query, post_data)
				updatedposts.append(posts['postid'])
			except Exception as e:
				print e,"for postid "+posts['postid']
			dbs.commit()
			cursor.close()
		print "%s Posts Saved"%(len(savedposts))
		print "%s Posts Updated"%(len(updatedposts))

if __name__ == '__main__':
	starttime = datetime.datetime.now()
	print sys.argv
	if(len(sys.argv)>1):
		gobackdays = int(sys.argv[1])
	else:
		gobackdays = 7
	ig = InstagramScraper(gobackdays)
	ig.handle_instagram()
	endtime = datetime.datetime.now() - starttime
	print "Completed in {0} secs.".format(endtime.seconds)
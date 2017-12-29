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
from tracker.models import Handle, FacebookAccessToken, FacebookHandlePost, FacebookUser, Hashtag

from django.db import IntegrityError
import MySQLdb
import MySQLdb.cursors
import random
import requests
import gc
from urllib import urlencode,urlopen
import json
from tracker.mysql_helper import safe_insert, safe_update
import re

todaydate = datetime.datetime.today()
todaydate = datetime.date(todaydate.year,todaydate.month,todaydate.day)

dbs = MySQLdb.connect(host='localhost',user='tracker',passwd='tracker123',db='theseus_social',charset='utf8')

re_hash = re.compile(r'(?<=^|(?<=[^a-zA-Z0-9-_\.]))#([_A-Za-z]+[A-Za-z0-9]+)')

class FacebookHashtags:
	def __init__(self, gobackdays = 2):
		self._india_offset = timedelta(hours = 5,minutes = 30)
		sincedate = todaydate - datetime.timedelta(days = gobackdays)
		self.since = sincedate.strftime('%Y-%m-%d')
		self.fbapps = FacebookAccessToken.objects.filter(active = 1)
		self.appindex = 0
		self.hashtags = [hashtag.name for hashtag in Hashtag.objects.filter(active = 1)]
		# self.handle_facebook()

	def handle_facebook(self):
		self.handle_posts()
		dbs.close()

	def get_accesstoken(self):
		if len(self.fbapps)>0:
			if self.appindex == len(self.fbapps):
				self.appindex = 0
			self.fbapp = self.fbapps[self.appindex]
			current_token = self.fbapp.appid+"|"+self.fbapp.api_secret
			self.appindex += 1
			return current_token
		else:
			print "No Facebook Apps"
			return False

	def handle_posts(self):
		graphuserurl = "https://graph.facebook.com/%s/?fields=%s&access_token=%s"
		graphpostsurl = "https://graph.facebook.com/%s/feed/?since=%s&fields=%s&access_token=%s"
		fbhandles = Handle.objects.filter(platform_id = 1, status = 2)
		userfields = ['id','name','description','fan_count','talking_about_count','picture','is_verified']
		postfields = ['id','object_id','picture','from','message','created_time',
						'shares','type','status_type','link','comments.limit(1).summary(true)',
						'likes.limit(1).summary(true)']
		userfields_str = ','.join(userfields)
		postfields_str = ','.join(postfields)
		handle_no = 1
		self.requests = 0
		for handle in fbhandles:
			self.page = 0
			# appindex = random.randint(0,len(self._accessTokenlist)-1)
			current_token = self.get_accesstoken()
			if current_token:
				# self.graph = facebook.GraphAPI(access_token=current_token, version='2.7')
				userurl = graphuserurl % (handle.uniqueid, userfields_str, current_token)
				response = urlopen(userurl)
				self.requests += 1
				userdata = json.loads(response.read())
				if userdata.get("error"):
					print 'API URL==>\n%s'%(userurl)
					self.raise_apierror(userdata["error"])
					continue
				user = self.getUser(handle,userdata,userurl)
				if not user:
					continue

				current_token = self.get_accesstoken()
				posturl = graphpostsurl % (handle.uniqueid, self.since, postfields_str, current_token)
				response = urlopen(posturl)
				self.requests += 1
				postdata = json.loads(response.read())
				if postdata.get("error"):
					print 'API URL==>\n%s'%(posturl)
					self.raise_apierror(postdata["error"])
					continue
				# pp.pprint(postdata)
				# break
				# postdata = self.graph.get_object(id=handle.uniqueid+'/feed',since=self.since,fields=','.join(postfields))
				self.getPosts(handle,postdata,posturl)
				print "REQUESTS: %s"%(self.requests)
				print "HANDLE NO: %s"%(handle_no)
				handle_no += 1
				print "sleep\n"
				sleep(3)

	def raise_apierror(self, err):
		errormsg = err.get("message","HTTP ERROR")
		message = "%s: %s"%(datetime.datetime.now(), errormsg)
		self.fbapp.usage_stats = message
		self.fbapp.save()
		print message+"\n"

	def getUser(self, handle, data, apiurl='firsturl'):
		print "HANDLE ==> %s %s"%(handle.id, handle.name)
		print 'API URL==>\n%s'%(apiurl)
		if data.get("id"):
			userdetails = {}
			userdetails['uniqueid'] = data['id']
			userdetails['name'] = data['name'].encode('unicode_escape')
			userdetails['description'] = data.get("description","")[:500].encode('unicode_escape')
			userdetails['likes'] = data['fan_count']
			userdetails['talkingabout'] = data['talking_about_count']
			try:
				userdetails['picture'] = data['picture']['data']['url']
			except KeyError:
				userdetails['picture'] = ""
			userdetails['verified'] = data['is_verified']
			# pp.pprint(userdetails)
		else:
			print "User Data Not Found"
			return False
		cursor = dbs.cursor()
		try:
			user_query,user_data = safe_insert("tracker_facebookuser",userdetails)
			cursor.execute(user_query, user_data)
			# FacebookUser(**userdetails).save()
			print 'Saved Facebook User: %s'%(userdetails['uniqueid'])
		except MySQLdb.IntegrityError:
			uniquecolumns = ["uniqueid"]
			user_query,user_data = safe_update("tracker_facebookuser",uniquecolumns,userdetails)
			cursor.execute(user_query, user_data)
			# FacebookUser.objects.filter(uniqueid=userdetails['uniqueid']).update(**userdetails)
			print 'Updated Facebook User: %s'%(userdetails['uniqueid'])
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
			next = requests.get(data['paging']['next']).json()
			apiurl = data['paging']['next']
			self.requests += 1
			self.page += 1
			print "REQUESTS: %s"%(self.requests)
			print 'Next Page: %s'%(self.page)
			self.getPosts(handle,next,apiurl)
		except:
			print "Posts Retrieved Since %s"%(self.since)
			print "HANDLE %s: Next not found, %s Pages Found"%(handle.name,self.page)

	def getComments(self, postid):
		comments = self.graph.get_connections(id=postid,connection_name='comments',
								fields='like_count,comment_count,message,created_time,from')
		pp.pprint(comments)

	def savePosts(self, handle, postslist):
		savedposts = []
		updatedposts = []
		for p in postslist:
			posts = {}
			
			posts['handle_id'] = handle.id
			posts['likes'] = 0
			posts['comments'] = 0
			posts['likes'] = p['likes']['summary']['total_count']
			posts['comments'] = p['comments']['summary']['total_count']

			posts['addedtime'] = datetime.datetime.now()
			posts['postid'] = postid = p.get('object_id','None')
			posts['fbgraph_id']  = p.get('id').split('_')[1]

			if(postid=='None'):					
				posts['postid'] = postid = posts['fbgraph_id']
			
			posts['message'] = message = p.get('message','None')
			if(message == 'None'):
				posts['message'] = message = p.get('story','')
			posts['hashtags'] = self.get_hashtags(posts['message'])

			hashtags = [h.lower() for h in posts['hashtags'].split(",")]
			htcount = 0
			for ht in hashtags:
				if ht in self.hashtags:
					htcount += 0
			if htcount == 0:
				continue

			posts['message'] = posts['message'].encode('unicode_escape')[:255]
			
			if 'updated their cover photo' in posts['message']:
			    print 'Ignoring and not saving this post::',posts['message']
			    continue 

			posts['author'] = p.get('from').get('id')	
			posts['url'] = postlink = "http://www.facebook.com/"+str(posts['author'])+'/posts/'+str(posts['fbgraph_id'])
			posts['postimg'] = p.get('picture',0)
			
			raw_published = p.get('created_time')
			dt_published = datetime.datetime(*time.strptime(raw_published,'%Y-%m-%dT%H:%M:%S+0000')[0:6])
			indiatz_published = dt_published+self._india_offset
			posts['published'] = indiatz_published
			posts['published_date'] = indiatz_published.strftime('%Y-%m-%d')
			posts['lastupdated'] = datetime.datetime.now()
			# posts['lastupdated'] = datetime.datetime.now() - datetime.timedelta(hours=8)  #New posts are now available for comments n likes updation
			# shares = p.get('shares',0)
			shares = p.get('shares',0)
			if(shares != 0):
				shares = shares.get('count')
			posts['shares'] = shares
			posts['posttype'] = p.get('type')
			posts['statustype'] = p.get('status_type')
			
			
			if(posts['author'] == handle.uniqueid):
				posts['fanpost'] = 0
			else:
				posts['fanpost'] = 1
			posts['tagged'] = 0
			posts['active'] = True
			cursor = dbs.cursor()
			try:
				post_query,post_data = safe_insert("tracker_facebookhandlepost",posts)
				cursor.execute(post_query, post_data)		
				# FacebookHandlePost(**posts).save()
				savedposts.append(posts['fbgraph_id'])
			except MySQLdb.IntegrityError:
				uniquecolumns = ["handle_id","fbgraph_id"]
				post_query,post_data = safe_update("tracker_facebookhandlepost",uniquecolumns,posts)
				cursor.execute(post_query, post_data)
				# FacebookHandlePost.objects.filter(handle_id=handle.id,fbgraph_id=posts['fbgraph_id']).update\
				# 								(posttype=posts['posttype'],statustype=posts['statustype'],
				# 								likes=posts['likes'],comments=posts['comments'],
				# 								shares=posts['shares'],lastupdated=posts['lastupdated'])
				updatedposts.append(posts['fbgraph_id'])
			except Exception as e:
				print e,"for postid "+posts['fbgraph_id']
			dbs.commit()
			cursor.close()
			# self.getComments(posts['fbgraph_id'])
			# gc.collect()
		print "%s Posts Saved"%(len(savedposts))
		print "%s Posts Updated"%(len(updatedposts))

	def get_hashtags(self, post):
		hashes = ",".join([hsh.strip('#').encode('unicode_escape') for hsh in re_hash.findall(post)])
		return hashes

if __name__ == '__main__':
	starttime = datetime.datetime.now()
	print sys.argv
	if(len(sys.argv)>1):
		gobackdays = int(sys.argv[1])
	else:
		gobackdays = 2
	fs = FacebookHashtags(gobackdays)
	fs.handle_facebook()
	endtime = datetime.datetime.now() - starttime
	print "Completed in {0} secs.".format(endtime.seconds)
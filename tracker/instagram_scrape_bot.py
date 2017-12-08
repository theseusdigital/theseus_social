import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import random
import datetime
from datetime import timedelta
from urllib import urlencode,urlopen
import httplib2
import json
from tracker.models import Handle

import pprint
pp = pprint.PrettyPrinter(indent=4)

from django.db import IntegrityError
import MySQLdb
import MySQLdb.cursors
from tracker.mysql_helper import safe_insert, safe_update
import re

todaydate = datetime.datetime.today().date()

india_offset = timedelta(hours = 5,minutes = 30)
dbs = MySQLdb.connect(host='localhost',user='theseus',passwd='theseus123',db='theseus_social',charset='utf8')
re_hash = re.compile(r'(?<=^|(?<=[^a-zA-Z0-9-_\.]))#([_A-Za-z]+[A-Za-z0-9]+)')

class InstagramScraper:
	def __init__(self, gobackdays = 7):
		self.since = todaydate - datetime.timedelta(days = gobackdays)
		self.postdetailsurl = "https://api.instagram.com/oembed/?url=%s"
		self.http = httplib2.Http()
		self.init_driver()

	def init_driver(self):
		self.driver = webdriver.Firefox()

	def handle_instagram(self):
		self.handle_posts()
		self.driver.quit()
		dbs.close()

	def getUser(self, handle):
		# userdetails = {}
		# userdetails['uniqueid'] = handle.uniqueid
		# headerpath = ".//*[@id='react-root']/section/main/article/header/section/"
		# try:
		# 	for i in range(1,4):
		# 		metricobj = self.driver.find_element_by_xpath(headerpath+"ul/li[%s]/span"%(i))
		# 		metric = metricobj.text.split(' ')[-1]
		# 		metrictitle = self.driver.find_element_by_xpath(headerpath+"ul/li[%s]/span/span"%(i)).get_attribute("title")
		# 		if metrictitle:
		# 			metricscore = int(metrictitle.replace(',',''))
		# 		else:
		# 			metricscore = int(metricobj.text.split(' ')[0].replace(',',''))
		# 		if metric == "following":
		# 			metric = "friends"
		# 		userdetails[str(metric)] = metricscore
		# 	userdetails["name"] = self.driver.find_element_by_xpath(headerpath+"div[2]/h1").text
		# 	userdetails["description"] = self.driver.find_element_by_xpath(headerpath+"div[2]/span/span").text[:500]
		# 	try:
		# 		userdetails["picture"] = self.driver.find_element_by_xpath(".//*[@id='react-root']/section/main/article/header/div/div/img").get_attribute("src")
		# 	except:
		# 		userdetails["picture"] = ""
		# except WebDriverException, e:
		# 	print e
		# 	return False

		handle_query = handle.name
		igurl =  "https://www.instagram.com/%s/?__a=1"
		igurl = igurl % (handle_query)
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
		return True

	def handle_posts(self):
		ighandleurl = 'https://www.instagram.com/%s'
		ighandles = Handle.objects.filter(platform_id = 4, status__in = [1,2])
		for handle in ighandles:
			print "Loading Page for HANDLE %s"%(handle.name)
			self.handle = handle
			igurl = ighandleurl % (handle.name)
			self.driver.get(igurl)
			waitseconds = random.randint(5,10)
			print 'Waiting for ',waitseconds
			time.sleep(waitseconds)
			print self.driver.current_url

			'''Get Handle User Data'''
			user = self.getUser(handle)
			if not user:
				continue

			totalcols = 3
			totalrows = 4
			loading = 0
			rownumber = 1

			lastpostdate = 0
			self.savedposts = 0
			self.updatedposts = 0
			totalposts = 0
			getPosts = True

			while rownumber <= totalrows:
				columnnumber = 1
				while columnnumber <= totalcols:
					igpost = {}
					xpathid = ".//*[@id='react-root']/section/main/article/div/div[1]/div["+str(rownumber)+"]/div["+str(columnnumber)+"]/a[1]"
					# print xpathid
					try:
					    scrollelement = self.driver.find_element_by_xpath(xpathid)
					except Exception as e:
					    print e
					    getPosts = False
					    break
					time.sleep(2)
					scrollelement.click()
					time.sleep(3)
					postlb_time = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[2]/div[2]/a/time").get_attribute('datetime') 
					post_time = datetime.datetime(*time.strptime(postlb_time,'%Y-%m-%dT%H:%M:%S.000Z')[0:6])
					post_time = post_time + india_offset
					post_date = post_time.date()
					lastpostdate = post_date
					if lastpostdate < self.since:
					    # print "Posts Retrieved Since %s"%(self.since)
					    break

					post_url = self.driver.current_url.split("?")[0]
					try:  
						post_message = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[2]/div[1]/ul/li[1]/span").text
					except:
						post_message = ""
					post_hashtags = self.get_hashtags(post_message)
					post_message = post_message.encode('unicode_escape')[:255]

					try:
						'''if it shows n Likes or n Views'''
						post_numbers_obj = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[2]/section[2]/div/span")
						post_numbers = post_numbers_obj.text
						post_metric = post_numbers.split(' ')[-1]
						post_score = int(post_numbers.split(' ')[0].replace(',',''))
					except:
						'''if likes are very less'''
						post_numbers_obj = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[2]/section[2]/div")
						post_numbers = post_numbers_obj.get_attribute("innerHTML")
						post_metric = "likes"
						post_score = int(len(post_numbers.split("/a>")) - 1)

					if post_metric == "likes":
						post_type = "image"
						post_likes = post_score
						post_views = 0
					else:
						post_type = "video"
						post_views = post_score
						'''getting likes for video posts'''
						try:
							post_numbers_obj.click()
							post_likes = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[2]/section[2]/div/div/div[4]/span").text
							post_likes = int(post_likes.replace(',',''))
						except:
							post_likes = 0

					if post_type == "image":
						'''getting image url'''
						try:
							post_img = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[1]/div/div[1]/div[1]/img").get_attribute('src')
						except:
							try:
								post_img = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[1]/div/div[1]/div[1]/div[1]/img").get_attribute('src')
							except:
								try:
									post_img = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[1]/div/div[1]/div[1]/div[1]/div[1]/img").get_attribute('src')
								except:
									post_img = ""
					else:
						'''getting video thumbnail image & video url'''
						try:
							post_img = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[1]/div/div[1]/div[1]/div[1]/div[1]/div[1]/video").get_attribute('poster')
							post_video = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[1]/div/div[1]/div[1]/div[1]/div[1]/div[1]/video").get_attribute('src')
						except:
							post_img = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[1]/div/div[1]/div[1]/div[1]/div[1]/video").get_attribute('poster')
							post_video = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[1]/div/div[1]/div[1]/div[1]/div[1]/video").get_attribute('src')

					try:
						'''if it shows "View All n Comments"'''
						comments_li = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[2]/div[1]/ul/li[2]/a").text
						if "View all" in comments_li:
							post_comments = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[2]/div[1]/ul/li[2]/a/span").text
							post_comments = int(post_comments)
						else:
							if "Load more" in comments_li:
								try:
									loaded = False
									print "Loading more comments"
									while True:
										loadmorebutton = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[2]/div[1]/ul/li[2]/a")
										time.sleep(2)
										loadmorebutton.click()
										if loaded:
											break
										time.sleep(3)
										buttontext = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[2]/div[1]/ul/li[2]/a").text
										if "View all" in buttontext:
											print buttontext
											loaded = True
									commentsoffset = 2
								except:
									commentsoffset = 3
							else:
								commentsoffset = 2

							'''if comments are very less or not truncated'''
							try:
								post_comments = self.driver.find_element_by_xpath("html/body/div[4]/div/div[2]/div/article/div[2]/div[1]/ul").get_attribute("innerHTML")
							except:
								post_comments = ""

							commentslist = post_comments.split("</li>")        
							if post_message == '':
							    commentsoffset = 1

							if len(commentslist)>1:
							    post_comments = len(commentslist) - commentsoffset
							else:
							    post_comments = 0

					except:
						print "No Comments"
						post_comments = 0

					url = self.postdetailsurl % (post_url)
					response,content = self.http.request(uri=url, method='GET')
					json_data = json.loads(content)

					try:
					    mediaid = json_data['media_id'].split('_')[0]
					    post_authorid = json_data['author_id']
					except:
					    mediaid = 0
					    post_authorid = 0

					igpost = {'handle_id':handle.id,'postid':mediaid,'caption':post_message,'tags':post_hashtags,'posttype':post_type,
								'url':post_url,'postimg':post_img,'author':post_authorid,'likes':post_likes,'views':post_views,
								'comments':post_comments,'published':post_time,'published_date':post_date,
								'lastupdated':datetime.datetime.now()}

					# pp.pprint(igpost)
					totalposts += 1
					self.savePost(igpost)
					print "%s %s Posts for HANDLE %s"%(post_url,totalposts,self.handle.name)

					exitpost = self.driver.find_element_by_xpath("html/body/div[4]/div/button")
					exitpost.click()
					columnnumber += 1

				rownumber += 1
				if lastpostdate < self.since or getPosts == False:
					print "\nlastpostdate: %s"%(lastpostdate)
					print "%s Posts & %s Rows Retrieved for Handle %s"%(totalposts, totalrows, handle.name)
					print "Posts Retrieved Since %s"%(self.since)
					break

				if lastpostdate >= self.since and rownumber > totalrows: # if the page has newer posts and it is the end of the page .. then click on loading or scroll more
					# loading += 1
					# if loading == 1:
					#     print "Loading more ....."                    
					#     # self._driver.find_element_by_xpath(".//*[@id='react-root']/section/main/article/div/div[3]/a").click() Commented this on 8th Feb 2017 and replaced with below
					#     driver.find_element_by_xpath(".//*[@id='react-root']/section/main/article/div/a").click()
					# else:
					self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
					print "\nScrolling down --> %s Posts & %s Rows Done \n"%(totalposts,totalrows)
					# time.sleep(2)
					totalrows += 4

			print "%s Posts Saved"%(self.savedposts)
			print "%s Posts Updated\n"%(self.updatedposts)

	def savePost(self, post):
		cursor = dbs.cursor()
		try:
			post_query,post_data = safe_insert("tracker_instagramhandlepost",post)
			cursor.execute(post_query, post_data)		
			self.savedposts += 1
		except MySQLdb.IntegrityError:
			'''not updating comments for api enabled handles i.e status=1'''
			if self.handle.status == 1:
				del post['comments']
			uniquecolumns = ["handle_id","postid"]
			post_query,post_data = safe_update("tracker_instagramhandlepost",uniquecolumns,post)
			cursor.execute(post_query, post_data)
			self.updatedposts += 1
		except Exception as e:
			print e,"for postid "+post['postid']
		dbs.commit()
		cursor.close()

	def get_hashtags(self, post):
		hashes = ",".join([hsh.strip('#').encode('unicode_escape') for hsh in re_hash.findall(post)])
		return hashes

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
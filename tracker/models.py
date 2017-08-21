# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.core import urlresolvers

# Create your models here.

def linked_url(urlhref, label):
	return '<a href="%s">%s</a>' % (urlhref, label)

def linked_template(iterlist, model):
	hrefs = []
	for o in iterlist:
		href = urlresolvers.reverse(model, args=(o.pk,))
		hrefs.append(linked_url(href, o.name))
	
	return ' | '.join(hrefs)

def linked_fields_template(model, field):
	if field == "keyword":
		field_objects = model.keyword.all()
	elif field == "handle":
		field_objects = model.handle.all()
	elif field == "platform":
		field_objects = model.platform.all()
	
	return linked_template(field_objects, 'admin:tracker_%s_change'%(field))

class Platform(models.Model):
	name = models.CharField(max_length=100, unique=True)
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.name

class Geo(models.Model):
	name = models.CharField(max_length=100, unique=True)
	abbr = models.CharField(max_length=5, unique=True)
	location = models.CharField(max_length=50, blank=True, null=True)

	def __str__(self):
		return self.name

class Keyword(models.Model):
	name = models.CharField(max_length=200, unique=True)
	active = models.BooleanField(default=True)
	max_tweet_id = models.BigIntegerField(default=0, db_index=True)
	platform = models.ManyToManyField(Platform, default='', blank=True)

	def linked_platforms(self):
		return linked_fields_template(self, 'platform')
	linked_platforms.short_description = 'Platforms'
	linked_platforms.allow_tags = True

	def __str__(self):
		return self.name

class Handle(models.Model):
	name = models.CharField(max_length=255)
	platform = models.ForeignKey(Platform,db_index=True)
	keyword = models.ForeignKey(Keyword,db_index=True)
	uniqueid = models.CharField(max_length=255, blank=True)
	max_tweet_id = models.BigIntegerField(default=0,db_index=True)
	status = models.IntegerField(default=1)

	class Meta:
		unique_together = (('name', 'platform'),)

	def __str__(self):
		return self.name+':'+self.platform.name

class Brand(models.Model):
	name = models.CharField(max_length=255, unique=True)
	handle = models.ManyToManyField(Handle, default='', blank=True)
	active = models.BooleanField(default=True)

	def linked_handles(self):
		return linked_fields_template(self, 'handle')
	linked_handles.short_description = 'Brand Handles'
	linked_handles.allow_tags = True

	def __str__(self):
		return self.name

class User(models.Model):
	username = models.CharField(max_length=255)
	password = models.CharField(max_length=200)
	active = models.BooleanField(default=True)
	handle = models.ManyToManyField(Handle, default='', blank=True)
	keyword = models.ManyToManyField(Keyword, default='', blank=True)

	def linked_handles(self):
		return linked_fields_template(self, 'handle')
	linked_handles.short_description = 'User Handles'
	linked_handles.allow_tags = True

	def linked_keywords(self):
		return linked_fields_template(self, 'keyword')
	linked_keywords.short_description = 'User Keywords'
	linked_keywords.allow_tags = True

	def __str__(self):
		return self.username

class FacebookAccessToken(models.Model):
	owner = models.CharField(max_length=60)
	appname = models.CharField(max_length=60, unique=True)
	appid = models.CharField(max_length=60, unique=True)
	api_secret = models.CharField(max_length=60, unique=True)
	usage_stats = models.CharField(max_length=500, null=True, blank=True)
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.appname

class TwitterAccessToken(models.Model):
	owner = models.CharField(max_length=60)
	appname = models.CharField(max_length=60)
	api_key = models.CharField(max_length=60, unique=True)
	api_secret = models.CharField(max_length=60, unique=True)
	access_token = models.CharField(max_length=60, unique=True)
	access_token_secret = models.CharField(max_length=60, unique=True)
	usage_stats = models.CharField(max_length=500, null=True, blank=True)
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.appname

class GoogleAccessToken(models.Model):
	owner = models.CharField(max_length=60)
	projectname = models.CharField(max_length=60, unique=True)
	api_key = models.CharField(max_length=60, unique=True)
	usage_stats = models.CharField(max_length=500, null=True, blank=True)
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.projectname

class InstagramAccessToken(models.Model):
	owner = models.CharField(max_length=60)
	appname = models.CharField(max_length=60)
	client_id = models.CharField(max_length=60, unique=True)
	client_secret = models.CharField(max_length=60, unique=True)
	access_token = models.CharField(max_length=60, unique=True)
	usage_stats = models.CharField(max_length=500, null=True, blank=True)
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.appname

class FacebookUser(models.Model):
	uniqueid = models.BigIntegerField(db_index=True, unique=True)
	name = models.CharField(max_length=200)
	description = models.CharField(max_length=1000,default="")
	likes = models.BigIntegerField(default=0)
	talkingabout = models.BigIntegerField(default=0)
	picture = models.CharField(max_length=1024,default="")
	verified = models.BooleanField()

class FacebookHandlePost(models.Model):
	handle = models.ForeignKey(Handle,db_index=True)
	postid = models.BigIntegerField(default=0)
	fbgraph_id = models.BigIntegerField(default=0,unique=True)    
	posttype = models.CharField(max_length=50)
	statustype = models.CharField(max_length=50)
	fanpost = models.BooleanField(default=True)
	message = models.CharField(max_length=255)
	url = models.CharField(max_length=1024)
	postimg = models.CharField(max_length=1024,default=0)
	author = models.BigIntegerField()
	likes = models.IntegerField(default=0)
	comments = models.IntegerField(default=0)
	shares = models.IntegerField(default=0)
	published = models.DateTimeField(db_index=True)
	published_date = models.DateField(db_index=True)
	addedtime = models.DateTimeField(db_index=True)
	lastupdated = models.DateTimeField(db_index=True)
	tagged = models.IntegerField(default=0,db_index=True)

class SocialMediaFacebook(models.Model):
	handle = models.ForeignKey(Handle, db_index=True, default = 1)
	reportdate = models.DateField(db_index=True)
	pagelikes = models.BigIntegerField(default=0)
	newpagelikes = models.IntegerField(default=0)
	postlikes = models.IntegerField(default=0)
	brandposts = models.IntegerField(default=0)
	fanposts = models.IntegerField(default=0)
	comments = models.IntegerField(default=0)
	shares = models.IntegerField(default=0)

	class Meta:
		unique_together = (('handle', 'reportdate'),)

class FacebookDailyNums(models.Model):
	handle = models.ForeignKey(Handle,db_index=True)
	likes = models.BigIntegerField(default=0)
	talkingabout = models.IntegerField(default=0)
	addedtime = models.DateField()

	class Meta:
		unique_together = (('handle', 'addedtime'),)

class TwitterUser(models.Model):
	user_id = models.BigIntegerField(db_index=True, unique=True)
	name = models.CharField(max_length=200)
	screen_name = models.CharField(max_length=200)
	created_at = models.DateTimeField()
	statuses_count = models.BigIntegerField()
	description = models.CharField(max_length=1000)
	followers_count = models.IntegerField()
	favorites_count = models.IntegerField()
	listed_count = models.IntegerField()
	friends_count = models.IntegerField()
	profile_image_url = models.CharField(max_length=1000)
	utc_offset = models.IntegerField()
	time_zone = models.CharField(max_length=200, db_index=True)
	location = models.CharField(max_length=200, db_index=True)
	verified = models.BooleanField()
	lang = models.CharField(max_length=10)
	lastupdated = models.DateTimeField(default=timezone.now)

	def __str__(self):
		return self.name

class HandleTweet(models.Model):
	geo_id = models.IntegerField(db_index=True, default=1)
	handle = models.ForeignKey(Handle, db_index=True)
	user_id = models.BigIntegerField()
	text = models.CharField(max_length=1024)
	tweet_id = models.BigIntegerField(db_index=True)
	in_reply_to_user_id = models.BigIntegerField()
	in_reply_to_status_id = models.BigIntegerField()
	favorite_count = models.BigIntegerField()
	favorited = models.BooleanField()
	retweet_count = models.PositiveIntegerField(default=0, db_index=True)
	retweeted = models.BooleanField()
	created_at = models.DateTimeField('tweet time', db_index=True)
	insert_time = models.DateTimeField('inserted time')
	lang = models.CharField(max_length=10)
	entities_hashtags = models.CharField(max_length=500)
	entities_urls = models.CharField(max_length=500)
	entities_user_mentions = models.CharField(max_length=500)
	entities_media = models.CharField(max_length=500)

	class Meta:
		unique_together = (('handle', 'tweet_id'),)

class HashtagUser(models.Model):
	user_id = models.BigIntegerField(db_index=True, unique=True)
	name = models.CharField(max_length=200)
	screen_name = models.CharField(max_length=200)
	created_at = models.DateTimeField()
	statuses_count = models.BigIntegerField()
	description = models.CharField(max_length=1000)
	followers_count = models.IntegerField()
	favorites_count = models.IntegerField()
	listed_count = models.IntegerField()
	friends_count = models.IntegerField()
	profile_image_url = models.CharField(max_length=1000)
	utc_offset = models.IntegerField()
	time_zone = models.CharField(max_length=200, db_index=True)
	location = models.CharField(max_length=200, db_index=True)
	verified = models.BooleanField()
	lang = models.CharField(max_length=10)
	lastupdated = models.DateTimeField(default=timezone.now)

	def __str__(self):
		return self.name

class Hashtag(models.Model):
	name = models.CharField(max_length=255, unique=True)
	max_tweet_id = models.BigIntegerField(default=0,db_index=True)
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.name

class HashtagTweet(models.Model):
	geo_id = models.IntegerField(db_index=True, default=1)
	hashtag = models.ForeignKey(Hashtag, db_index=True)
	user_id = models.BigIntegerField()
	text = models.CharField(max_length=1024)
	tweet_id = models.BigIntegerField(db_index=True)
	in_reply_to_user_id = models.BigIntegerField()
	in_reply_to_status_id = models.BigIntegerField()
	favorite_count = models.BigIntegerField()
	favorited = models.BooleanField()
	retweet_count = models.PositiveIntegerField(default=0, db_index=True)
	retweeted = models.BooleanField()
	created_at = models.DateTimeField('tweet time', db_index=True)
	insert_time = models.DateTimeField('inserted time')
	lang = models.CharField(max_length=10)
	entities_hashtags = models.CharField(max_length=500)
	entities_urls = models.CharField(max_length=500)
	entities_user_mentions = models.CharField(max_length=500)
	entities_media = models.CharField(max_length=500)
	active = models.BooleanField(db_index=True, default=False)

	class Meta:
		unique_together = (('hashtag', 'tweet_id'),)

class TwitterDailyNums(models.Model):
	handle = models.ForeignKey(Handle,db_index=True)
	tweets = models.IntegerField(default=0)
	followers = models.BigIntegerField(default=0)
	favorites = models.IntegerField(default=0)
	following = models.BigIntegerField(default=0)
	addedtime = models.DateField()

	class Meta:
		unique_together = (('handle', 'addedtime'),)

class SocialMediaTwitter(models.Model):
	handle = models.ForeignKey(Handle, db_index=True, default = 1)
	reportdate = models.DateField(db_index=True)
	followers = models.BigIntegerField(default=0)
	newfollowers = models.IntegerField(default=0)
	tweets = models.IntegerField(default=0)
	retweets = models.IntegerField(default=0)
	favorites = models.IntegerField(default=0)

	class Meta:
		unique_together = (('handle', 'reportdate'),)
	
class TwitterTweet(models.Model):
	geo_id = models.IntegerField(db_index=True, default=1)
	keyword = models.ForeignKey(Keyword, db_index=True)
	user_id = models.BigIntegerField()
	text = models.CharField(max_length=1024)
	tweet_id = models.BigIntegerField(db_index=True)
	in_reply_to_user_id = models.BigIntegerField()
	in_reply_to_status_id = models.BigIntegerField()
	favorite_count = models.BigIntegerField()
	favorited = models.BooleanField()
	retweet_count = models.PositiveIntegerField(default=0, db_index=True)
	retweeted = models.BooleanField()
	created_at = models.DateTimeField('tweet time', db_index=True)
	insert_time = models.DateTimeField('inserted time')
	lang = models.CharField(max_length=10)
	entities_hashtags = models.CharField(max_length=500)
	entities_urls = models.CharField(max_length=500)
	entities_user_mentions = models.CharField(max_length=500)
	entities_media = models.CharField(max_length=500)
	summerized = models.BooleanField(db_index=True, default=False)

	class Meta:
		unique_together = (('keyword', 'tweet_id'),)

class YoutubeChannel(models.Model):
	handle = models.ForeignKey(Handle)
	etag = models.CharField(max_length=200)
	playlist = models.CharField(max_length=200)
	youtubeid = models.CharField(max_length=80, unique=True)
	title = models.CharField(max_length=800)
	description = models.TextField()
	comments = models.IntegerField()
	subscribers = models.BigIntegerField()
	videos = models.IntegerField()
	views = models.BigIntegerField()
	published = models.DateTimeField()

class YoutubeChannelVideo(models.Model):
	handle = models.ForeignKey(Handle, db_index=True)
	etag = models.CharField(max_length=200)
	youtubeid = models.CharField(max_length=80, unique=True)
	title = models.CharField(max_length=800)
	description = models.TextField()
	comments = models.IntegerField()
	views = models.BigIntegerField()
	likes = models.IntegerField()
	dislikes = models.IntegerField()
	favorites = models.IntegerField()
	sharedonfb = models.IntegerField(default=0)
	published = models.DateTimeField(db_index=True)

class YoutubeDailyNums(models.Model):
	handle = models.ForeignKey(Handle,db_index=True)
	videos = models.IntegerField(default=0)
	views = models.BigIntegerField(default=0)
	subscribers = models.IntegerField(default=0)
	comments = models.IntegerField(default=0)
	addedtime = models.DateField()

	class Meta:
		unique_together = (('handle', 'addedtime'),)

class SocialMediaYoutube(models.Model):
	handle = models.ForeignKey(Handle, db_index=True, default = 1)
	reportdate = models.DateField(db_index=True)
	alltimeviews = models.BigIntegerField(default=0)
	newviews = models.BigIntegerField(default=0)
	views = models.BigIntegerField(default=0)
	subscribers = models.BigIntegerField(default=0)
	newsubscribers = models.IntegerField(default=0)
	videos = models.IntegerField(default=0)
	likes = models.IntegerField(default=0)
	dislikes = models.IntegerField(default=0)
	comments = models.IntegerField(default=0)

	class Meta:
		unique_together = (('handle', 'reportdate'),)

class InstagramUser(models.Model):
	uniqueid = models.BigIntegerField(db_index=True,unique=True)
	name = models.CharField(max_length=200)
	description = models.CharField(max_length=1000,default="")
	posts = models.BigIntegerField(default=0)
	friends = models.BigIntegerField(default=0)
	followers = models.BigIntegerField(default=0)
	picture = models.CharField(max_length=1024,default="")

class InstagramHandlePost(models.Model):
	handle = models.ForeignKey(Handle,db_index=True)
	postid = models.BigIntegerField(default=0,unique=True)  
	posttype = models.CharField(max_length=50)
	caption = models.CharField(max_length=255)
	url = models.CharField(max_length=1024)
	postimg = models.CharField(max_length=1024,default=0)
	author = models.BigIntegerField()
	likes = models.IntegerField(default=0)
	comments = models.IntegerField(default=0)
	tags = models.CharField(max_length=500)
	published = models.DateTimeField(db_index=True)
	published_date = models.DateField(db_index=True)
	lastupdated = models.DateTimeField(db_index=True)

class InstagramDailyNums(models.Model):
	handle = models.ForeignKey(Handle,db_index=True)
	posts = models.IntegerField(default=0)
	friends = models.BigIntegerField(default=0)
	followers = models.BigIntegerField(default=0)
	addedtime = models.DateField()

	class Meta:
		unique_together = (('handle', 'addedtime'),)

class SocialMediaInstagram(models.Model):
	handle = models.ForeignKey(Handle, db_index=True, default = 1)
	reportdate = models.DateField(db_index=True)
	followers = models.BigIntegerField(default=0)
	newfollowers = models.IntegerField(default=0)
	posts = models.IntegerField(default=0)
	likes = models.IntegerField(default=0)
	comments = models.IntegerField(default=0)

	class Meta:
		unique_together = (('handle', 'reportdate'),)
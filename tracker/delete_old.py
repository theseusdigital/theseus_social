import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

import datetime
from datetime import timedelta
from tracker.models import FacebookHandlePost, HandleTweet, YoutubeChannelVideo
import pprint
pp = pprint.PrettyPrinter(indent=4)
import time

todaydate = datetime.datetime.today()
todaydate = datetime.date(todaydate.year,todaydate.month,todaydate.day)

class DeleteOld():
    def __init__(self, gobackdays = 90):
        sincedate = todaydate - datetime.timedelta(days = gobackdays)
        self.since = sincedate.strftime('%Y-%m-%d')+" 00:00:00"

    def handleplatforms(self):
        self.deletefacebook()
        self.deletetwitter()
        self.deleteyoutube()
        print "DELETED ROWS BEFORE %s"%(self.since)

    def deletefacebook(self):
        delete_count = FacebookHandlePost.objects.filter(published__lt = self.since).count()
        FacebookHandlePost.objects.filter(published__lt = self.since).delete()
        print "DELETED %s FACEBOOK POSTS"%(delete_count)

    def deletetwitter(self):
        delete_count = HandleTweet.objects.filter(created_at__lt = self.since).count()
        HandleTweet.objects.filter(created_at__lt = self.since).delete()
        print "DELETED %s TWITTER TWEETS"%(delete_count)

    def deleteyoutube(self):
        delete_count = YoutubeChannelVideo.objects.filter(published__lt = self.since).count()
        YoutubeChannelVideo.objects.filter(published__lt = self.since).delete()
        print "DELETED %s YOUTUBE VIDEOS"%(delete_count)
        
if __name__ == '__main__':
    starttime = datetime.datetime.now()
    print sys.argv
    if(len(sys.argv)>1):
        gobackdays = int(sys.argv[1])
    else:
        gobackdays = 90
    deleteold = DeleteOld(gobackdays)
    deleteold.handleplatforms()
    endtime = datetime.datetime.now() - starttime
    print "Completed in {0} secs.".format(endtime.seconds)
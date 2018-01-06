import sys, os, django
# sys.path.append("/home/nishant/theseus_social") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theseus_social.settings")
django.setup()

# Import smtplib for the actual sending function
import smtplib
# For guessing MIME type
import mimetypes
# Import the email modules we'll need
import email
import email.mime.application
from email.header import Header
from email.utils import formataddr

import datetime
from datetime import timedelta
from tracker.models import FacebookHandlePost, HandleTweet, YoutubeChannelVideo, InstagramHandlePost,\
                            FacebookDailyNums, TwitterDailyNums, YoutubeDailyNums, InstagramDailyNums
import pprint
pp = pprint.PrettyPrinter(indent=4)
import time

class ScrapeStatus():
    def __init__(self):
        self.todaydate = datetime.datetime.today().date()
        self.since = "%s 00:00:00"%(self.todaydate)
        self.obtain_scrape_status()

    def obtain_scrape_status(self):
        facebook_count = FacebookHandlePost.objects.filter(published__gte = self.since).count()
        twitter_count = HandleTweet.objects.filter(created_at__gte = self.since).count()
        youtube_count = YoutubeChannelVideo.objects.filter(published__gte = self.since).count()
        instagram_count = InstagramHandlePost.objects.filter(published__gte = self.since).count()
        facebook_dailynums = FacebookDailyNums.objects.filter(addedtime = self.todaydate).count()
        twitter_dailynums = TwitterDailyNums.objects.filter(addedtime = self.todaydate).count()
        youtube_dailynums = YoutubeDailyNums.objects.filter(addedtime = self.todaydate).count()
        instagram_dailynums = InstagramDailyNums.objects.filter(addedtime = self.todaydate).count()
        self.statuses = [
                {"table":"tracker_facebookhandlepost","records":facebook_count},
                {"table":"tracker_handletweet","records":twitter_count},
                {"table":"tracker_youtubechannelvideo","records":youtube_count},
                {"table":"tracker_instagramhandlepost","records":instagram_count},
                {"table":"tracker_facebookdailynums","records":facebook_dailynums},
                {"table":"tracker_twitterdailynums","records":twitter_dailynums},
                {"table":"tracker_youtubedailynums","records":youtube_dailynums},
                {"table":"tracker_instagramdailynums","records":instagram_dailynums}
        ]
        self.scrape_html = self.prepare_for_email()

    def prepare_for_email(self):
        html = [
            '<table style="" border="1">'
            '<tr><th>Tablename</th><th>Records</th><th>Since(date)</th></tr>'
            ]
        tablerow = '<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>'
        
        for status in self.statuses:
            print "%s ==> %s"%(status['table'], status['records'])
            html.append(tablerow.format(status['table'],status['records'],self.todaydate))
        html.append('</table>')
        
        return ''.join(html)

    def send_email(self):
        message = self.scrape_html
        receivers = "nishantshetty92@gmail.com,tech@theseus.digital"
        sender = formataddr((str(Header(u'Theseus Tracker', 'utf-8')), "nishant.theseus@gmail.com"))
        # Create a text/plain message
        msg = email.mime.Multipart.MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receivers
        msg['Subject'] = 'Scrape Status Report'
        # The main body is just another attachment
        body = email.mime.Text.MIMEText(message,'html')
        msg.attach(body)
        # server = smtplib.SMTP('localhost')
        server = smtplib.SMTP('smtp.gmail.com:587')
        username = 'nishant.theseus@gmail.com'
        password = 'theseus123'
        server.ehlo()
        server.starttls()
        server.login(username,password)
        server.sendmail(sender,receivers.split(","), msg.as_string())
        server.quit()

        print 'Scrape Status Sent Successfully'

        
if __name__ == '__main__':
    scrapestatus = ScrapeStatus()
    scrapestatus.send_email()
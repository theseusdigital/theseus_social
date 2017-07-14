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
from tracker.facebook_scrape import FacebookScraper
from tracker.twitter_scrape import TwitterScraper
from tracker.youtube_scrape import YoutubeScraper

class HandleScraper:
	def __init__(self):
		self.scrape_platforms()

	def scrape_platforms(self):
		self.scrape_facebook()
		self.scrape_twitter()
		self.scrape_youtube()

	def scrape_facebook(self):
		fs = FacebookScraper()
		fs.handle_facebook()

	def scrape_twitter(self):
		fs = TwitterScraper()
		fs.handle_twitter()

	def scrape_youtube(self):
		ys = YoutubeScraper()
		ys.handle_youtube()

	def bulk_insert_or_update(self, db_table, create_fields, update_fields, values):
		cursor = db.cursor()

		# if len(values) == 0:
		#     transaction.commit_unless_managed()
		#     return

		values_sql = ["(%s)" % (','.join(["%s"] * len(create_fields)),)]

		base_sql = "INSERT INTO %s (%s) VALUES " % (db_table, ",".join(create_fields))
		            
		on_duplicates = []

		for field in update_fields:
		    on_duplicates.append(field + "=VALUES(" + field +")")

		sql = "%s %s ON DUPLICATE KEY UPDATE %s" % (base_sql, ", ".join(values_sql), ",".join(on_duplicates))

		cursor.executemany(sql, values)
		# transaction.commit_unless_managed()

if __name__ == '__main__':
	hs = HandleScraper()
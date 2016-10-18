
#!/usr/bin/env python

import tweepy
import csv
import time
import re
import codecs, cStringIO
from argparse import ArgumentParser


class UTF8Recoder:
	"""
	Iterator that reads an encoded stream and reencodes the input to UTF-8
	"""
	def __init__(self, f, encoding):
		self.reader = codecs.getreader(encoding)(f)

	def __iter__(self):
		return self


	def next(self):
		return self.reader.next().encode("utf-8")



class UnicodeWriter:
	"""
	A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
	"""
	def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
		#Redirect output to a queue
		self.queue = cStringIO.StringIO()
		self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
		self.stream = f
		self.encoder = codecs.getincrementalencoder(encoding)()

	def writerow(self, row):
		self.writer.writerow([s.encode("utf-8") for s in row])
		# Fetch UTF-8 output from the queue ...
		data = self.queue.getvalue()
		data = data.decode("utf-8")
		# ... and reencode it into the target encoding
		data = self.encoder.encode(data)
		# write to the target stream
		self.stream.write(data)
		# empty queue
		self.queue.truncate(0)

	def writerows(self, rows):
		for row in rows:
			self.writerow(row)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '-u',
        '--max_users',
        help='Max amount of followers to return.',
        type=int,
        default=4000,
        metavar='max_users'
    )
    parser.add_argument(
        '-a',
        '--account',
        help='Twitter account to get followers from.',
        type=str,
        metavar='account'
    )
    parser.add_argument(
        'file_path',
        help='Input csv file to process.',
        metavar='path'
    )
    return parser.parse_args()


def get_friends_descriptions(api,file_path, twitter_account, max_users):
	"""
	Return the bios of the people that a user follows
    api -- the tweetpy API object
    twitter_account -- the Twitter handle of the user
    max_users -- the maximum amount of users to return
	"""

	user_ids = []

	try:
		for page in tweepy.Cursor(api.followers_ids, id=twitter_account, count=5000).pages():
			user_ids.extend(page)

	except tweepy.RateLimitError:
		print "RateLimitError...waiting 1000 seconds to continue"
		time.sleep(1000)
		for page in tweepy.Cursor(api.followers_ids, id=twitter_account, count=5000).pages():
			user_ids.extend(page)

	following = []

	for start in xrange(0, min(max_users, len(user_ids)), 100):
		end = start + 100

		try:
			following.extend(api.lookup_users(user_ids[start:end]))
		except tweepy.RateLimitError:
			print "RateLimitError...waiting 1000 seconds to continue"
			time.sleep(1000)
			following.extend(api.lookup_users(user_ids[start:end]))

	with open(file_path, 'w') as f:
		writer = UnicodeWriter(f)
		for user in following:
			writer.writerow([user.screen_name, user.description])

def tw_oauth(authfile):
    with open(authfile, "r") as f:
        ak = f.readlines()
    f.close()
    auth1 = tweepy.auth.OAuthHandler(ak[0].replace("\n",""), ak[1].replace("\n",""))
    auth1.set_access_token(ak[2].replace("\n",""), ak[3].replace("\n",""))
    return tweepy.API(auth1)


if __name__ == "__main__":
	# OAuth key file
	authfile = './auth.k'
	api = tw_oauth(authfile)


	args = parse_args()
	print 
	get_friends_descriptions(api,args.file_path, args.account, max_users=args.max_users)

    
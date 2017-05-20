import os
import time
import urllib
from random import random
from twython import Twython
from face import update_image

CONSUMER_KEY = os.environ['TWITTER_CONSUMER_KEY']
CONSUMER_SECRET = os.environ['TWITTER_CONSUMER_SECRET']
OAUTH_TOKEN = os.environ['TWITTER_OAUTH_TOKEN']
OAUTH_TOKEN_SECRET = os.environ['TWITTER_OAUTH_TOKEN_SECRET']

TWEET_LENGTH = 140
TWEET_URL_LENGTH = 21
RUN_EVERY_N_SECONDS = 60*60 # e.g. 60*5 = tweets every five minutes

def twitter_handle():
    return Twython(CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

def favorite_tweet(tweet, handle):
    handle.create_favorite(id=tweet['id'])

def already_replied(tweet, handle):
    # if we favorited this tweet already, then we've replied
    return tweet['favorited']

def get_image_in_tweet(tweet):
    """
    n.b. can also append sizes to url
        sizes: tweet['entities']['media'][0]['sizes'].keys()
        e.g. http://pbs.twimg.com/media/DAMpysCUMAE3SlL.jpg:thumb
    """
    try:
        url = tweet['entities']['media'][0]['media_url']
        name, headers = urllib.urlretrieve(url)
        return name, url
    except:
        return None, None

def reply_with_image(tweet, infile, url, handle):
    # reply to tweet with the processed image
    message = '@' + tweet['user']['screen_name']
    # image = update_image(infile)
    outfile = update_image(infile, url)
    if outfile is not None:
        image_ids = handle.upload_media(media=open(outfile))
        handle.update_status(status=message,
            media_ids=image_ids['media_id'],
            in_reply_to_status_id=tweet['id'])
    else:
        print 'Ignoring tweet with no faces in image'

def get_mentions(handle):
    # returns iterator of tweets mentioning us
    return handle.cursor(handle.get_mentions_timeline, include_entities=True)

def main():
    handle = twitter_handle()
    while True:
        for tweet in get_mentions(handle):
            time.sleep(RUN_EVERY_N_SECONDS)
            if already_replied(tweet, handle):
                print 'Ignoring tweet because I already replied.'
                continue
            infile, url = get_image_in_tweet(tweet)
            if infile:
                print "Replying to tweet id {}...".format(tweet['id'])
                reply_with_image(tweet, infile, url, handle)
                favorite_tweet(tweet, handle) # to mark as replied
            else:
                print 'Ignoring tweet without image'

if __name__ == '__main__':
    main()

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
        message = "Sorry, I couldn't find a face in that image. " + message
        handle.update_status(status=message,
            in_reply_to_status_id=tweet['id'])
        print 'Ignoring tweet with no faces in image'

def get_mentions(handle):
    # returns iterator of tweets mentioning us
    return handle.cursor(handle.get_mentions_timeline, include_entities=True)

def find_random_tweet_with_image(handle, max_tries=10):
    i = 0
    for tweet in handle.cursor(handle.search, q='photo', result_type='popular', include_entities=True):
        infile, url = get_image_in_tweet(tweet)
        if infile is not None and not already_replied(tweet, handle):
            return infile, url, tweet
        i += 1
        if i > max_tries:
            return None, None, None

def tweet_random_image(handle):
    infile, url, tweet = find_random_tweet_with_image(handle)
    if infile is None:
        return
    outfile = update_image(infile, url)
    if outfile is None:
        print 'Ignoring tweet with no faces in image'
        return
    image_ids = handle.upload_media(media=open(outfile))
    message = ' '
    handle.update_status(status=message,
        media_ids=image_ids['media_id'])
    favorite_tweet(tweet, handle)

RUN_EVERY_N_SECONDS = 60*1 # e.g. 60*5 = tweets every five minutes
MAX_SKIPS = 30 # if no tweets in a while, tweet something random
def main():
    handle = twitter_handle()
    tweet_random_image(handle)
    while True:
        i = 0        
        for tweet in get_mentions(handle):
            time.sleep(RUN_EVERY_N_SECONDS)
            if already_replied(tweet, handle):
                print 'Ignoring tweet {} because I already replied.'.format(tweet['id'])
                # might break once I reach this point, since it probably means I've reached the most recent ones
                i += 1
                if i > MAX_SKIPS:
                    tweet_random_image(handle)
                continue
            i = 0
            infile, url = get_image_in_tweet(tweet)
            if infile:
                print "Replying to tweet {}...".format(tweet['id'])
                reply_with_image(tweet, infile, url, handle)
                favorite_tweet(tweet, handle) # to mark as replied
                # handle.create_friendship(screen_name=tweet['user']['screen_name'])
            else:
                print 'Ignoring tweet {} without image'.format(tweet['id'])

if __name__ == '__main__':
    main()

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
    try:
        handle.create_favorite(id=tweet['id'])
    except:
        return

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

def get_start_id(handle):
    xs = handle.get_favorites(count=1)
    if not xs:
        return None
    return xs[0]['id']

def find_random_tweet_with_image(handle, tweets_seen, max_tries=2):
    i = 0
    for tweet in handle.cursor(handle.search, q='photo', result_type='popular', include_entities=True):
        infile, url = get_image_in_tweet(tweet)
        if infile is None or already_replied(tweet, handle) or tweet['id'] in tweets_seen:
            i += 1
            if i > max_tries:
                return None, None, None
            continue
        return infile, url, tweet
    return None, None, None

def tweet_random_image(handle, tweets_seen):
    infile, url, tweet = find_random_tweet_with_image(handle, tweets_seen)
    if infile is None:
        return tweet
    outfile = update_image(infile, url)
    if outfile is None:
        print 'Ignoring tweet {} with no faces in image'.format(tweet['id'])
        return tweet
    image_ids = handle.upload_media(media=open(outfile))
    message = ' '
    handle.update_status(status=message,
        media_ids=image_ids['media_id'])
    favorite_tweet(tweet, handle)
    return tweet

RUN_EVERY_N_SECONDS = 60*5 # e.g. 60*5 = tweets every five minutes
MAX_SKIPS = 20 # if no tweets in a while, tweet something random
def main():
    handle = twitter_handle()
    tweets_seen = []
    while True:
        i = 0
        # start_id = get_start_id(handle)
        for tweet in handle.cursor(handle.get_mentions_timeline, include_entities=True):
            time.sleep(RUN_EVERY_N_SECONDS)
            if tweet['id'] in tweets_seen or already_replied(tweet, handle):
                print 'Seen tweet {} already.'.format(tweet['id'])
                i += 1
                if i > MAX_SKIPS:
                    tweets_seen.append(tweet_random_image(handle, tweets_seen))
                    i = 0
                continue
            i = 0
            infile, url = get_image_in_tweet(tweet)
            if infile:
                print "Replying to tweet {}...".format(tweet['id'])
                reply_with_image(tweet, infile, url, handle)
                favorite_tweet(tweet, handle) # to mark as replied
            else:
                print 'Ignoring tweet {} without image'.format(tweet['id'])
            tweets_seen.append(tweet['id'])

if __name__ == '__main__':
    main()

import time
import logging

from datetime import datetime

from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim

from factcheckers import domains

geolocator = Nominatim(user_agent='twitter_replies_app')

def condense_tweet(tw, bare_retweet=False, tw_sub=None):
    if bare_retweet:
        text = 'RT'
    elif tw_sub is None:
        text = tw['extended_tweet']['full_text'] if tw['truncated'] else tw['text']
    else:
        text = tw_sub['extended_tweet']['full_text'] if tw_sub['truncated'] else tw_sub['text']

    tweet_dict = {
        'id': tw['id'],
        'text': text,
        'lang': tw['lang'],
        'created_at': datetime.strptime(tw['created_at'], '%a %b %d %H:%M:%S %z %Y'),
        'user_verified': tw['user']['verified'],
        'user_followers': tw['user']['followers_count'],
        'country': tw['user']['location']
    }

    return tweet_dict

def contains_factcheck_link(tweet):
    if 'urls' in tweet:
        if tweet['urls'] == []:
            return False
        else:
            link = tweet['urls'][0]['expanded_url']
            return any(domain in link for domain in domains)
    else:
        return False

def contains_factcheck(tweet):
    factcheck = False
    if 'urls' in tweet and tweet['urls'] != []:
        if contains_factcheck_link(tweet):
            factcheck = True
    return factcheck

def get_link_quote(tw):
    if 'quoted_status' not in tw:
        return None
    if 'extended_tweet' in tw['quoted_status']:
        links = tw['quoted_status']['extended_tweet']['entities']['urls']
    else:
        links = tw['quoted_status']['entities']['urls']
    if links == []:
        return None
    else:
        return links[0]['expanded_url']

def get_link_retweet(tw):
    if 'extended_tweet' in tw['retweeted_status']:
        links = tw['retweeted_status']['extended_tweet']['entities']['urls']
    else:
        links = tw['retweeted_status']['entities']['urls']
    if links == []:
        return None
    else:
        return links[0]['expanded_url']

def to_geocode(address, attempt=1, max_attempts=0, timeout=1):
    try:
        return geolocator.geocode(address)

    except GeocoderTimedOut:
        if attempt <= max_attempts:
            time.sleep(timeout)
            return to_geocode(address, attempt=attempt+1, timeout=timeout+1)
        raise
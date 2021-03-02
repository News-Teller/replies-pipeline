from datetime import datetime
from factcheckers import domains

def condense_tweet(tw):
    text = tw['extended_tweet']['full_text'] if tw['truncated'] else tw['text']

    tweet_dict = {
        'id': tw['id'],
        'text': text,
        'lang': tw['lang'],
        #'reply_count': tw['reply_count'],
        #'retweet_count': tw['retweet_count'],
        #'favorite_count': tw['favorite_count'],
        'created_at': datetime.strptime(tw['created_at'], '%a %b %d %H:%M:%S %z %Y'),
        # 'is_quote_status': tw['is_quote_status'],
        'user_verified': tw['user']['verified'],
        'user_followers': tw['user']['followers_count']
    }

    return tweet_dict

def condense_retweet(tw):
    text = tw['retweeted_status']['extended_tweet']['full_text'] if tw['retweeted_status']['truncated'] else \
    tw['retweeted_status']['text']

    tweet_dict = {
        'id': tw['id'],
        'original_id': tw['retweeted_status']['id'],
        'text': text,
        'lang': tw['lang'],
        #'reply_count': tw['reply_count'],
        #'retweet_count': tw['retweet_count'],
        #'favorite_count': tw['favorite_count'],
        'created_at': datetime.strptime(tw['created_at'], '%a %b %d %H:%M:%S %z %Y'),
        # 'is_quote_status': tw['is_quote_status'],
        'user_verified': tw['user']['verified'],
        'user_followers': tw['user']['followers_count'] # importance of user: verified, followers_count
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
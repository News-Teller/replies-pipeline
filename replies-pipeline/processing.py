import os
import logging
import queue #from multiprocessing import Process, Queue
from transformers import pipeline
from strdistance import jaro_sim
from helpers import *
from keywords import *

import psycopg2
import psycopg2.extras
from psycopg2.extras import execute_values

BATCH_SIZE_SENTIMENT = 20
BATCH_SIZE_INSERT = 50


try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=os.getenv('POSTGRES_PORT', '5430'),
        dbname=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres')
    )
    conn.autocommit = True
    logging.info("== DB connection established ==")
except psycopg2.OperationalError as err:
    logging.error(err)


classifier = pipeline("zero-shot-classification")
sent_hypothesis_template = "The sentiment of this tweet is {}."
sent_candidate_labels = ["positive", "negative"]


def sentiment_analysis(q_sent, q_geo):
    for_analysis = []

    while True:
        if not q_sent.empty():
            tweet = q_sent.get()
            for_analysis.append(tweet)
        
        if len(for_analysis) > BATCH_SIZE_SENTIMENT:
            time.sleep(3)
            
            text_only = []

            for el in for_analysis:
                text_only.append(el['text'])
            
            s_a = classifier(text_only, sent_candidate_labels, hypothesis_template=sent_hypothesis_template)

            for i, el in enumerate(s_a, start=0):
                pos_score = el['scores'][(el['labels'].index('positive'))]
                neg_score = el['scores'][(el['labels'].index('negative'))]
                
                for_analysis[i]['positive_score'] = pos_score
                for_analysis[i]['negative_score'] = neg_score

            logging.warning('Sentiment metrics calculated for ', len(to_sa), 'tweets')
            
            for el in for_analysis:
                q_geo.put(el)
            
            for_analysis[:] = []
    
    return

def get_country_code(cities, countries, address):
    if address is None:
        return None
    
    address_list = (address.replace(',', '').lower()).split()

    for word in address_list:
        if word in countries:
            return str(countries[word])
    for word in address_list:
        if word in cities:
            return str(cities[word])
    
    if len(address) < 4:
        return None

    try:
        loc = to_geocode(address)
        if loc is None:
            return None
        
        code = geolocator.reverse((loc.raw['lat'], loc.raw['lon']), language='en').raw['address']['country_code']
        tweet['country'] = code

    except Exception as exc:
        logging.warning("Geocoding failed: %s" % exc)
        return None

def geolocalize(q_geo, q_ins):
    # Load toponymic data
    with open('../geodata/cities.json') as json_file:
        cities = json.load(json_file)
    with open('../geodata/countries_all.json') as json_file:
        countries = json.load(json_file)
    
    while True:
        if not q_geo.empty():
            tweet = q_geo.get()
            address = tweet['country']
            tweet['country'] = get_country_code(cities, countries, address)
            q_ins.put(tweet)
    
    return

def insert_bunch(q_ins):
    to_insert = []

    while True:
        if not q_ins.empty():
            tweet = q_ins.get()
            tweet['keywords'] = get_keywords(tweet['text'], tweet['lang'])

            to_insert.append(tweet)

        if len(to_insert) > BATCH_SIZE_INSERT:
            with conn.cursor() as cur:
                try:
                    """
                    columns = to_insert[0].keys()
                    query = 'INSERT INTO public."Tweets" ({}) VALUES %s'.format(','.join(columns))
                    values = [[value for value in mini_tweet.values()] for mini_tweet in to_insert]
                    execute_values(cur, query, values)
                    conn.commit()
                    """
                    print('Inserted', len(to_insert))
                except Exception as exc:
                    logging.warning("Error executing SQL: %s" % exc)
                finally:
                    to_insert[:] = []
    
    return

def process_tweet(tweet, q_sent, q_geo):
    # Check if tweet is a reply
    if tweet['in_reply_to_status_id'] is not None:

        factcheck = contains_factcheck(tweet_full) # factchecking flag

        tweet = condense_tweet(tweet)

        tweet_small['factchecked'] = factcheck
        tweet_small['reply_to'] = tweet['in_reply_to_status_id']
        tweet_small['retweet_of'] = None
        
    elif tweet_full['is_quote_status'] and 'retweeted_status' in tweet_full:
        # RT d'Q
        retweeted_status = tweet['retweeted_status']['extended_tweet']['full_text'] \
            if tweet['retweeted_status']['truncated'] else \
                tweet['retweeted_status']['text']
        
    elif tweet_full['is_quote_status'] in tweet_full:
        text = tweet['extended_tweet']['full_text'] if tweet['truncated'] else \
                tweet['text']
        original = tweet['quoted_status_id']

        #link = get_link_retweet(tweet)
        #if link is not None:
        #    return
        
        factcheck = contains_factcheck(tweet_full) # factchecking flag

        tweet = condense_tweet(tweet)

        tweet_small['factchecked'] = factcheck
        tweet_small['reply_to'] = None
        tweet_small['retweet_of'] = tweet['quoted_status_id']
    else:
        text = tweet['extended_tweet']['full_text'] if tweet['truncated'] else \
                tweet['text']
        original = tweet['quoted_status_id']

        #link = get_link_retweet(tweet)
        #if link is not None:
        #    return
        
        factcheck = contains_factcheck(tweet_full) # factchecking flag

        tweet = condense_tweet(tweet)

        tweet_small['factchecked'] = factcheck
        tweet_small['reply_to'] = None
        tweet_small['retweet_of'] = tweet['retweeted_status']['id']

    q_sent.put(tweet_small)

    return

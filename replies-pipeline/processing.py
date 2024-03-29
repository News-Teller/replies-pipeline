import os
import json
import logging
from multiprocessing import Process, Queue
from transformers import pipeline
from strdistance import jaro_sim
from helpers import *
from keywords import *

import psycopg2
import psycopg2.extras
from psycopg2.extras import execute_values

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.WARNING,
    datefmt='%Y-%m-%d %H:%M:%S')

BATCH_SIZE_SENTIMENT = 30
BATCH_SIZE_INSERT = 100


try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=os.getenv('POSTGRES_PORT', '5430'),
        dbname=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres')
    )
    conn.autocommit = True
    logging.info('== DB connection established ==')
    
except psycopg2.OperationalError as err:
    logging.error(err)


def sentiment_analysis(q_sent, q_geo, q_ins):
    classifier = pipeline('zero-shot-classification')
    sent_hypothesis_template = "The sentiment of this tweet is {}."
    sent_candidate_labels = ['positive', 'negative']

    for_analysis = []

    while True:
        if not q_sent.empty():
            tweet = q_sent.get()
            for_analysis.append(tweet)
        
        if len(for_analysis) > BATCH_SIZE_SENTIMENT:
            text_only = []

            for el in for_analysis:
                text_only.append(el['text'])
            
            s_a = classifier(text_only, sent_candidate_labels, hypothesis_template=sent_hypothesis_template)

            for i, el in enumerate(s_a, start=0):
                pos_score = el['scores'][(el['labels'].index('positive'))]
                #neg_score = el['scores'][(el['labels'].index('negative'))]
                
                for_analysis[i]['positive_score'] = pos_score
            
            for el in for_analysis:
                address = el['country']
                if address is not None:
                    if len(address) > 4:
                        q_geo.put(el)
                else:
                    el['country'] = None
                    q_ins.put(el)
            
            logging.info( 'Sentiment metrics calculated for {} tweets'.format(str(BATCH_SIZE_SENTIMENT)) )
            
            for_analysis[:] = []
    
    return

def get_country_code(cities, countries, address):
    if address is None:
        return None
    
    address_list = (address.replace(',', '').lower()).split()

    for word in address_list:
        if word in countries:
            logging.info('Geolocated by country')
            return str(countries[word])
    for word in address_list:
        if word in cities:
            logging.info('Geolocated by city')
            return str(cities[word])
    
    if len(address) < 4:
        return None

    try:
        loc, geolocator = to_geocode(address)
        if loc is None:
            return None
        #time.sleep(0.05)
        code = geolocator.reverse((loc.raw['lat'], loc.raw['lon']), language='en').raw['address']['country_code']
        logging.info('Tweet geocoded')
        return code

    except Exception as exc:
        logging.info("Geocoding failed: %s" % exc)
        return None

def geolocalize(q_geo, q_ins):
    # Load toponymic data
    with open('geodata/cities.json') as json_file:
        cities = json.load(json_file)
    with open('geodata/countries_all.json') as json_file:
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
            if 'keywords' not in tweet:
                tweet['keywords'] = get_keywords(tweet['text'], tweet['lang'])
            else:
                kw = get_keywords(tweet['keywords'], tweet['lang'])
                tweet['keywords'] = kw

            to_insert.append(tweet)

        if len(to_insert) > BATCH_SIZE_INSERT:
            with conn.cursor() as cur:
                try:
                    columns = to_insert[0].keys()
                    query = 'INSERT INTO public."Tweets" ({}) VALUES %s'.format(','.join(columns))
                    values = [[mini_tweet[value] for value in columns] for mini_tweet in to_insert]
                    execute_values(cur, query, values)
                    conn.commit()

                    logging.warning('> Inserted {} tweets'.format(BATCH_SIZE_INSERT))
                    
                except Exception as exc:
                    logging.warning("Error executing SQL: %s" % exc)
                finally:
                    to_insert[:] = []
    
    return

def process_tweet(tweet, q_sent, q_geo):
    # Check if tweet is a reply
    try:

        if tweet['in_reply_to_status_id'] is not None:
            tweet_small = condense_tweet(tweet)

            tweet_small['reply_to'] = tweet['in_reply_to_status_id']

            if not tweet['is_quote_status']:
                factcheck = contains_factcheck(tweet)
                tweet_small['factchecked'] = factcheck
                tweet_small['retweet_of'] = None
            else:
                tweet_small['factchecked'] = True
                tweet_small['retweet_of'] = tweet['quoted_status_id']
                tweet_small['keywords'] = ''.join([tweet['text'], ': \"', tweet['quoted_status']['text'], '\"'])

            q_sent.put(tweet_small)

        # RT of a Quote
        elif tweet['is_quote_status'] and 'retweeted_status' in tweet:
            user = tweet['user']
            retweeted = tweet['retweeted_status']
            retweeted['user'] = user

            tweet_small = condense_tweet(retweeted)
            factcheck = contains_factcheck(retweeted)
            tweet_small['factchecked'] = factcheck
            tweet_small['retweet_of'] = retweeted['quoted_status_id']
            tweet_small['reply_to'] = None

            if 'quoted_status' in tweet:
                tweet_small['keywords'] = tweet['quoted_status']['text']
            else:
                tweet_small['keywords'] = tweet_small['text']

            q_sent.put(tweet_small)

        # Quote    
        elif tweet['is_quote_status'] in tweet:
            text = tweet['extended_tweet']['full_text'] if tweet['truncated'] else \
                    tweet['text']

            tweet = condense_tweet(tweet)
            factcheck = contains_factcheck(tweet)
            tweet_small['factchecked'] = factcheck
            tweet_small['reply_to'] = None
            tweet_small['retweet_of'] = tweet['quoted_status_id']

            if 'quoted_status' in tweet:
                tweet_small['keywords'] = tweet_small['keywords'] = tweet['quoted_status']['text']
            else:
                tweet_small['keywords'] = tweet_small['text']

            q_sent.put(tweet_small)

        # Bare retweet
        elif 'retweeted_status' in tweet:
            tweet_small = condense_tweet(tweet, bare_retweet=True)

            tweet_small['factchecked'] = False
            tweet_small['reply_to'] = None
            tweet_small['retweet_of'] = tweet['retweeted_status']['id']
            tweet_small['keywords'] = tweet['retweeted_status']['text']
            
            tweet_small['positive_score'] = None
            #tweet_small['negative_score'] = None

            q_geo.put(tweet_small)
    
    except Exception as exc:
        logging.warning(exc)   
    
    return

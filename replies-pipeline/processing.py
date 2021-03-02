import os
import logging
from multiprocessing import Process, Queue
from transformers import pipeline
from strdistance import jaro_sim
from helpers import *
from keywords import *

import psycopg2
import psycopg2.extras
from psycopg2.extras import execute_values

BATCH_SIZE = 100

try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        dbname=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres')
    )
    conn.autocommit = True
    logging.info("== DB connection established ==")
except psycopg2.OperationalError as err:
    logging.error(err)

q_insert_list = []

classifier = pipeline('sentiment-analysis')

def sentiment_analysis(q):
    while True:
        if not q.empty():
            tw = q.get()

            s_a = classifier(tw['text'])[0]
            tw['sentiment_label'] = (1 if s_a['label'] == 'POSITIVE' else 0)
            tw['sentiment_score'] = s_a['score']
            logging.info('Sentiment metrics calculated')
            q_insert_list.append(tw)
            insert_bunch()

def insert_bunch():
    if len(q_insert_list) > BATCH_SIZE:
        with conn.cursor() as cur:
            try:
                columns = q_insert_list[0].keys()
                query = 'INSERT INTO public."Tweets" ({}) VALUES %s'.format(','.join(columns))
                values = [[value for value in q.values()] for q in q_insert_list]
                execute_values(cur, query, values)
                conn.commit()

                print("== INSERTED", len(q_insert_list))
                
            except Exception as exc:
                logging.warning("Error executing SQL: %s" % exc)
            finally:
                q_insert_list[:] = []
    return

def process_tweet(tweet, q):
    # checkig RT/Quote, quotes too similar = RT
    retweet = False
    if tweet['is_quote_status'] and 'quoted_status' in tweet:
        link = get_link_quote(tweet)
        tweet_small = condense_tweet(tweet)
        if link is not None:
            if jaro_sim(tweet['text'], tweet['quoted_status']['text']) >= 0.7:
                retweet = False  # True
        else:
            return  # if no link
    elif 'retweeted_status' in tweet:
        link = get_link_retweet(tweet)
        tweet_small = condense_retweet(tweet)
        if link is not None:
            retweet = True
        else:
            return
    else:
        return
    #tweet_small['link'] = link  # tweet_small['retweet'] = retweet
    factcheck = contains_factcheck(tweet) # factchecking flag
    tweet_small['factchecked'] = factcheck
    tweet_small['keywords'] = get_keywords(tweet_small['text'], tweet_small['lang'])

    q.put(tweet_small)

    return

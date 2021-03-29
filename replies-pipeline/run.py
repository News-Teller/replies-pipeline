import os
import json
from kafka import KafkaConsumer

from multiprocessing import Manager, Process, Queue

from processing import *

def main():
    consumer_tweets = KafkaConsumer(
        os.getenv('KAFKA_TOPIC', 'tweets'),
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVER', 'kafka:9092'),
        group_id=None,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        api_version=(2, 3, 0),
        consumer_timeout_ms=5000,
        auto_offset_reset='latest',
        enable_auto_commit=True)

    manager = Manager()
    queue_sentiment = manager.Queue()
    queue_location = manager.Queue()
    queue_insertion = manager.Queue()

    processes = []

    processes.append(Process(target=insert_bunch, args=(queue_insertion,)))
    processes.append(Process(target=geolocalize, args=(queue_location,queue_insertion,)))
    processes.append(Process(target=sentiment_analysis, args=(queue_sentiment,queue_location,)))
    processes.append(Process(target=sentiment_analysis, args=(queue_sentiment,queue_location,)))
    
    for p in processes:
        p.start()
    
    for msg in consumer_tweets:
        tweet_full = msg.value

        if tweet_full['lang'] not in spacy_models.keys() and tweet_full['lang'] is not None:
            continue

        process_tweet(tweet_full, queue_sentiment, queue_location)

    for p in processes:
        p.join()


if __name__ == "__main__":
    main()
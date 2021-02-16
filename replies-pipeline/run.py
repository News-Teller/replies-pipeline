import json
from multiprocessing import Process, Queue
from kafka import KafkaConsumer
from processing import *

def main():
    consumer_Tweets = KafkaConsumer('tweets',
                                    bootstrap_servers=['10.0.0.43:9096'],
                                    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                                    api_version=(2, 3, 0),
                                    consumer_timeout_ms=2000,
                                    auto_offset_reset='latest',
                                    enable_auto_commit=True, )
    q = Queue()
    proc = Process(target=sentiment_analysis, args=(q,))
    proc.start()
    it = 0
    for msg in consumer_Tweets:
        tweet_full = msg.value
        if it == 0:
            print('\n!!!!02')
            it += 1
        if tweet_full['lang'] != 'en' and tweet_full['lang'] is not None:
            continue
        process_tweet(tweet_full, q)

    proc.join()
    return


if __name__ == "__main__":
    main()
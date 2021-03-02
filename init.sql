GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
-- Table: public.Tweets
CREATE TABLE IF NOT EXISTS public."Tweets"
(
    id bigint,
    original_id bigint,
    text character varying(500) COLLATE pg_catalog."default",
    lang character varying(10) COLLATE pg_catalog."default",
--    reply_count integer,
--    retweet_count integer,
--    favorite_count integer,
    created_at date,
    user_verified boolean,
    user_followers integer,
--    link character varying(200) COLLATE pg_catalog."default",
    factchecked boolean,
    sentiment_label integer, --character varying(10) COLLATE pg_catalog."default",
    sentiment_score double precision,
    keywords character varying[] 
);

CREATE VIEW positives AS
SELECT id, original_id, text, lang, created_at, user_verified, user_followers, factchecked, sentiment_label, sentiment_score, keywords
	FROM public."Tweets"
	WHERE sentiment_label=1
	ORDER BY round( CAST(sentiment_score as numeric), 3)  DESC, (CASE when user_verified then 1 else 2 end) ASC, user_followers DESC, factchecked;

CREATE VIEW negatives AS
SELECT id, original_id, text, lang, created_at, user_verified, user_followers, factchecked, sentiment_label, sentiment_score, keywords
	FROM public."Tweets"
	WHERE sentiment_label=0
	ORDER BY round( CAST(sentiment_score as numeric), 3)  DESC, (CASE when user_verified then 1 else 2 end) ASC, user_followers DESC, factchecked;
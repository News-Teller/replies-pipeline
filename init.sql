GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
-- Table: public.Tweets
CREATE TABLE IF NOT EXISTS public."Tweets"
(
    id bigint,
    text character varying(500) COLLATE pg_catalog."default",
    lang character varying(10) COLLATE pg_catalog."default",
    created_at date,
    user_verified boolean,
    user_followers integer,
    reply_to bigint,
    retweet_of bigint,
    factchecked boolean,
    positive_score double precision,
    negative_score double precision,
    country character varying(10) COLLATE pg_catalog."default",
    keywords character varying[] COLLATE pg_catalog."default"
);

CREATE VIEW positives AS
SELECT id, text, lang, created_at, user_verified, user_followers, factchecked, positive_score, negative_score, country, keywords
	FROM public."Tweets"
	ORDER BY round( CAST(positive_score as numeric), 4)  DESC, (CASE when user_verified then 1 else 2 end) ASC, user_followers DESC, factchecked;

CREATE VIEW negatives AS
SELECT id, text, lang, created_at, user_verified, user_followers, factchecked, positive_score, negative_score, country, keywords
	FROM public."Tweets"
	ORDER BY round( CAST(negative_score as numeric), 4)  DESC, (CASE when user_verified then 1 else 2 end) ASC, user_followers DESC, factchecked;
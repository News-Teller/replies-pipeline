CREATE USER postgres;
CREATE DATABASE postgres;
GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
-- Table: public.Tweets
CREATE TABLE IF NOT EXISTS public."Tweets"
(
    id bigint,
    original_id bigint,
    text character varying(500) COLLATE pg_catalog."default",
    lang character varying(10) COLLATE pg_catalog."default",
    reply_count integer,
    retweet_count integer,
    favorite_count integer,
    created_at date,
    user_verified boolean,
    user_followers integer,
--    link character varying(200) COLLATE pg_catalog."default",
    factchecked boolean,
    sentiment_label integer, --character varying(10) COLLATE pg_catalog."default",
    sentiment_score double precision
);

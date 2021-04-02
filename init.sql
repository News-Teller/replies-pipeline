GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
-- Table: public.Tweets
CREATE TABLE IF NOT EXISTS public."Tweets"
(
    id bigint,
    text character varying(500) COLLATE pg_catalog."default",
    lang character varying(10) COLLATE pg_catalog."default",
    created_at timestamp with time zone,
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

CREATE OR REPLACE VIEW public."metrics"
 AS
 WITH quotes AS (
         SELECT t1.id,
            t1.retweet_of AS original,
            t1.created_at,
            t1.user_verified,
            t1.user_followers,
            t1.factchecked,
            t1.positive_score,
            t1.country,
            t1.keywords
           FROM public."Tweets" t1
          WHERE (((t1.text)::text <> 'RT'::text) AND (t1.retweet_of IS NOT NULL) AND (t1.reply_to IS NULL))
        ), rt_quotes AS (
         SELECT t1.id,
            t1.retweet_of AS original,
            t1.created_at,
            t1.user_verified,
            t1.user_followers,
            t1.factchecked,
            t1.positive_score,
            t1.country,
            t1.keywords
           FROM public."Tweets" t1
          WHERE ((t1.retweet_of IS NOT NULL) AND (t1.reply_to IS NOT NULL))
        ), replies AS (
         SELECT t1.id,
            t1.reply_to AS original,
            t1.created_at,
            t1.user_verified,
            t1.user_followers,
            t1.factchecked,
            t1.positive_score,
            t1.country,
            t1.keywords
           FROM public."Tweets" t1
          WHERE ((t1.retweet_of IS NULL) AND (t1.reply_to IS NOT NULL))
        ), bare_rts AS (
         SELECT t1.id,
            t1.retweet_of AS original,
            t1.created_at,
            t1.user_verified,
            t1.user_followers,
            t1.country,
            t1.keywords
           FROM public."Tweets" t1
          WHERE ((t1.text)::text = 'RT'::text)
        ), reactions AS (
         SELECT quotes.id,
            quotes.original,
            quotes.created_at,
            quotes.user_verified,
            quotes.user_followers,
            quotes.factchecked,
            quotes.positive_score,
            quotes.country,
            quotes.keywords
           FROM quotes
        UNION
         SELECT rt_quotes.id,
            rt_quotes.original,
            rt_quotes.created_at,
            rt_quotes.user_verified,
            rt_quotes.user_followers,
            rt_quotes.factchecked,
            rt_quotes.positive_score,
            rt_quotes.country,
            rt_quotes.keywords
           FROM rt_quotes
        UNION
         SELECT replies.id,
            replies.original,
            replies.created_at,
            replies.user_verified,
            replies.user_followers,
            replies.factchecked,
            replies.positive_score,
            replies.country,
            replies.keywords
           FROM replies
        ), pos AS (
         SELECT reactions.id,
            reactions.original,
            reactions.created_at,
            reactions.user_verified,
            reactions.user_followers,
            reactions.factchecked,
            reactions.positive_score,
            reactions.country,
            reactions.keywords
           FROM reactions
          WHERE (reactions.positive_score > (0.6)::double precision)
        ), neg AS (
         SELECT reactions.id,
            reactions.original,
            reactions.created_at,
            reactions.user_verified,
            reactions.user_followers,
            reactions.factchecked,
            reactions.positive_score,
            reactions.country,
            reactions.keywords
           FROM reactions
          WHERE (reactions.positive_score < (0.4)::double precision)
        ), reaction_stat AS (
         SELECT reactions.id,
            reactions.original,
                CASE
                    WHEN (reactions.positive_score > (0.6)::double precision) THEN 1
                    ELSE 0
                END AS pos,
                CASE
                    WHEN (reactions.positive_score < (0.4)::double precision) THEN 1
                    ELSE 0
                END AS neg,
                CASE
                    WHEN ((reactions.positive_score <= (0.6)::double precision) AND (reactions.positive_score >= (0.4)::double precision)) THEN 1
                    ELSE 0
                END AS neu
           FROM reactions
        ), discussion_stat AS (
         SELECT alle.original,
            min(alle.created_at) AS earliest,
            min(alle.created_at) AS latest,
            count(*) AS resonance,
            sum(
                CASE
                    WHEN (alle.user_followers > 0) THEN log((alle.user_followers)::double precision)
                    ELSE (0)::double precision
                END) AS resonance_adjusted,
            string_agg(DISTINCT (alle.country)::text, ', '::text) AS countries,
            count(DISTINCT alle.country) AS countries_count,
            count(
                CASE
                    WHEN alle.user_verified THEN 1
                    ELSE NULL::integer
                END) AS verified_users
           FROM ( SELECT reactions.id,
                    reactions.original,
                    reactions.created_at,
                    reactions.user_verified,
                    reactions.user_followers,
                    reactions.country,
                    reactions.keywords
                   FROM reactions
                UNION
                 SELECT bare_rts.id,
                    bare_rts.original,
                    bare_rts.created_at,
                    bare_rts.user_verified,
                    bare_rts.user_followers,
                    bare_rts.country,
                    bare_rts.keywords
                   FROM bare_rts) alle
          GROUP BY alle.original
        ), discussion_reaction AS (
         SELECT discussion_stat.original,
            discussion_stat.earliest,
            discussion_stat.latest,
            discussion_stat.resonance,
            discussion_stat.resonance_adjusted,
            discussion_stat.countries,
            discussion_stat.countries_count,
            discussion_stat.verified_users,
            rs.oid,
            rs.all_re,
            rs.pos_re,
            rs.neu_re,
            rs.neg_re,
            ((1)::double precision - ((abs((rs.pos_re - rs.neg_re)) + rs.neu_re) / rs.all_re)) AS controversiality
           FROM (discussion_stat
             JOIN ( SELECT reaction_stat.original AS oid,
                    (count(*))::double precision AS all_re,
                    (sum(reaction_stat.pos))::double precision AS pos_re,
                    (sum(reaction_stat.neu))::double precision AS neu_re,
                    (sum(reaction_stat.neg))::double precision AS neg_re
                   FROM reaction_stat
                  GROUP BY reaction_stat.original) rs ON ((rs.oid = discussion_stat.original)))
        )
 SELECT dr.original AS tweet_id,
    dr.earliest,
    dr.latest,
    dr.resonance,
    dr.resonance_adjusted,
    dr.pos_re,
    dr.neu_re,
    dr.neg_re,
    brt.bare_rts,
    dr.all_re,
    (dr.pos_re / dr.all_re) AS positivity,
    (dr.neg_re / dr.all_re) AS negativity,
    ((dr.neg_re + (brt.bare_rts)::double precision) / (dr.all_re + (brt.bare_rts)::double precision)) AS neutrality_abs,
    dr.controversiality,
    (dr.controversiality * log((dr.resonance)::double precision)) AS controversiality_adjusted,
    dr.countries,
    dr.countries_count
   FROM (discussion_reaction dr
     LEFT JOIN ( SELECT bare_rts.original,
            count(*) AS bare_rts
           FROM bare_rts
          GROUP BY bare_rts.original) brt ON ((dr.original = brt.original)))
  ORDER BY (dr.controversiality * (log((dr.resonance)::double precision) / (2)::double precision)) DESC;

ALTER TABLE public."metrics" OWNER TO postgres;
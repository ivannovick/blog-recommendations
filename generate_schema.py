#!/usr/bin/env python3
"""
Generate schema.sql with the current EMBEDDING_DIMENSIONS from config
"""
from config import EMBEDDING_DIMENSIONS

schema_template = """--
-- Greenplum Database database dump
--

-- Dumped from database version 12.22
-- Dumped by pg_dump version 12.22

SET gp_default_storage_options = '';
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;
SET gp_enable_statement_trigger = on;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: blog_cluster_summaries; Type: TABLE; Schema: public; Owner: gpadmin
--

CREATE TABLE public.blog_cluster_summaries (
    cluster_id integer NOT NULL,
    summary text,
    generated_at timestamp without time zone DEFAULT now()
) DISTRIBUTED BY (cluster_id);


ALTER TABLE public.blog_cluster_summaries OWNER TO gpadmin;

--
-- Name: blog_posts; Type: TABLE; Schema: public; Owner: gpadmin
--

CREATE TABLE public.blog_posts (
    id integer NOT NULL,
    category text,
    title text,
    description text,
    is_verified boolean,
    embedding public.vector({dimensions}),
    cluster_id integer
) DISTRIBUTED BY (id);


ALTER TABLE public.blog_posts OWNER TO gpadmin;

--
-- Name: blog_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: gpadmin
--

CREATE SEQUENCE public.blog_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 20;


ALTER TABLE public.blog_posts_id_seq OWNER TO gpadmin;

--
-- Name: blog_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gpadmin
--

ALTER SEQUENCE public.blog_posts_id_seq OWNED BY public.blog_posts.id;


--
-- Name: blog_posts id; Type: DEFAULT; Schema: public; Owner: gpadmin
--

ALTER TABLE ONLY public.blog_posts ALTER COLUMN id SET DEFAULT nextval('public.blog_posts_id_seq'::regclass);


--
-- Name: blog_cluster_summaries blog_cluster_summaries_pkey; Type: CONSTRAINT; Schema: public; Owner: gpadmin
--

ALTER TABLE ONLY public.blog_cluster_summaries
    ADD CONSTRAINT blog_cluster_summaries_pkey PRIMARY KEY (cluster_id);


--
-- Name: blog_posts blog_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: gpadmin
--

ALTER TABLE ONLY public.blog_posts
    ADD CONSTRAINT blog_posts_pkey PRIMARY KEY (id);


--
-- Greenplum Database database dump complete
--
"""

def generate_schema():
    """Generate schema.sql with current embedding dimensions"""
    schema = schema_template.replace('{dimensions}', str(EMBEDDING_DIMENSIONS))

    with open('schema.sql', 'w') as f:
        f.write(schema)

    print(f"✅ Generated schema.sql with embedding dimensions: {EMBEDDING_DIMENSIONS}")

if __name__ == "__main__":
    generate_schema()
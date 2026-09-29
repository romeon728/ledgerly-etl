--
-- PostgreSQL database dump
--

\restrict xtWAEOaQIIB8LZ5jOQjwwy01JFvvBqDo0xYZhTi8aTFGkhFeHUWRabFyOXp4Vja

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accounts; Type: TABLE; Schema: public; Owner: ledgerly
--

CREATE TABLE public.accounts (
    account_id integer NOT NULL,
    bank_name character varying(100) NOT NULL,
    account_type character varying(50) NOT NULL,
    last_four character varying(4) DEFAULT '0000'::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.accounts OWNER TO ledgerly;

--
-- Name: accounts_account_id_seq; Type: SEQUENCE; Schema: public; Owner: ledgerly
--

CREATE SEQUENCE public.accounts_account_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.accounts_account_id_seq OWNER TO ledgerly;

--
-- Name: accounts_account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ledgerly
--

ALTER SEQUENCE public.accounts_account_id_seq OWNED BY public.accounts.account_id;


--
-- Name: categories; Type: TABLE; Schema: public; Owner: ledgerly
--

CREATE TABLE public.categories (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    subcategory character varying(100) NOT NULL
);


ALTER TABLE public.categories OWNER TO ledgerly;

--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: public; Owner: ledgerly
--

CREATE SEQUENCE public.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categories_id_seq OWNER TO ledgerly;

--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ledgerly
--

ALTER SEQUENCE public.categories_id_seq OWNED BY public.categories.id;


--
-- Name: categorization_rules; Type: TABLE; Schema: public; Owner: ledgerly
--

CREATE TABLE public.categorization_rules (
    id integer NOT NULL,
    pattern character varying(255) NOT NULL,
    match_type character varying(20) DEFAULT 'contains'::character varying,
    target_merchant character varying(255) NOT NULL,
    target_category character varying(100) NOT NULL,
    target_subcategory character varying(100),
    priority integer DEFAULT 10,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.categorization_rules OWNER TO ledgerly;

--
-- Name: categorization_rules_id_seq; Type: SEQUENCE; Schema: public; Owner: ledgerly
--

CREATE SEQUENCE public.categorization_rules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categorization_rules_id_seq OWNER TO ledgerly;

--
-- Name: categorization_rules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ledgerly
--

ALTER SEQUENCE public.categorization_rules_id_seq OWNED BY public.categorization_rules.id;


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: ledgerly
--

CREATE TABLE public.transactions (
    transaction_id integer NOT NULL,
    account_id integer NOT NULL,
    posted_date date NOT NULL,
    description text NOT NULL,
    amount numeric(12,2) NOT NULL,
    merchant character varying(255),
    category character varying(100),
    subcategory character varying(100),
    source character varying(50) DEFAULT 'vllm_inference'::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.transactions OWNER TO ledgerly;

--
-- Name: transactions_transaction_id_seq; Type: SEQUENCE; Schema: public; Owner: ledgerly
--

CREATE SEQUENCE public.transactions_transaction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transactions_transaction_id_seq OWNER TO ledgerly;

--
-- Name: transactions_transaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ledgerly
--

ALTER SEQUENCE public.transactions_transaction_id_seq OWNED BY public.transactions.transaction_id;


--
-- Name: accounts account_id; Type: DEFAULT; Schema: public; Owner: ledgerly
--

ALTER TABLE ONLY public.accounts ALTER COLUMN account_id SET DEFAULT nextval('public.accounts_account_id_seq'::regclass);


--
-- Name: categories id; Type: DEFAULT; Schema: public; Owner: ledgerly
--

ALTER TABLE ONLY public.categories ALTER COLUMN id SET DEFAULT nextval('public.categories_id_seq'::regclass);


--
-- Name: categorization_rules id; Type: DEFAULT; Schema: public; Owner: ledgerly
--

ALTER TABLE ONLY public.categorization_rules ALTER COLUMN id SET DEFAULT nextval('public.categorization_rules_id_seq'::regclass);


--
-- Name: transactions transaction_id; Type: DEFAULT; Schema: public; Owner: ledgerly
--

ALTER TABLE ONLY public.transactions ALTER COLUMN transaction_id SET DEFAULT nextval('public.transactions_transaction_id_seq'::regclass);


--
-- Data for Name: accounts; Type: TABLE DATA; Schema: public; Owner: ledgerly
--

COPY public.accounts (account_id, bank_name, account_type, last_four, created_at) FROM stdin;
1	TD Bank	Savings	2766	2026-09-28 22:48:03.763329+00
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: ledgerly
--

COPY public.categories (id, name, subcategory) FROM stdin;
1	Housing	Rent & Mortgage
2	Housing	Other
3	Transportation	Automotive & Fuel
4	Transportation	Public Transit & Rideshare
5	Transportation	Other
6	Food & Dining	Groceries
7	Food & Dining	Restaurants & Coffee
8	Food & Dining	Other
9	Shopping	General Retail
10	Shopping	Other
11	Utilities & Bills	Utilities
12	Utilities & Bills	Subscriptions & Software
13	Utilities & Bills	Other
14	Entertainment	Subscriptions & Software
15	Entertainment	Other
16	Income	Payroll & Direct Deposit
17	Income	Other
18	Financial & Transfers	Account Transfer
19	Financial & Transfers	Other
20	Healthcare	Medical & Pharmacy
21	Healthcare	Other
25	Income	Transfer
26	Uncategorized	Other
31	Income	Interest
33	IRS	Taxes
34	IRS	Other
35	Financial & Transfers	Cash & ATM
37	Financial & Transfers	Fees & Service Charges
\.


--
-- Data for Name: categorization_rules; Type: TABLE DATA; Schema: public; Owner: ledgerly
--

COPY public.categorization_rules (id, pattern, match_type, target_merchant, target_category, target_subcategory, priority, created_at) FROM stdin;
1	Spotify	contains	Spotify	Entertainment	Subscriptions & Software	10	2026-09-28 04:26:34.763796+00
5	Online Xfer Transfer to CK x4642	exact	TD Bank	Income	Transfer	10	2026-09-29 00:22:20.551551+00
4	INTEREST CREDIT	exact	TD Bank	Income	Interest	10	2026-09-28 23:05:03.329689+00
7	STATE OF N.J.	contains	Governmant	IRS	Taxes	10	2026-09-29 02:08:06.556248+00
8	IRS	contains	Government	IRS	Taxes	10	2026-09-29 02:08:34.791401+00
9	WITHDRAW	contains	TD Bank	Financial & Transfers	Cash & ATM	10	2026-09-29 02:12:15.758779+00
10	ATM	contains	TD Bank	Financial & Transfers	Cash & ATM	10	2026-09-29 02:14:26.518715+00
11	MAINTENANCE FEE	exact	TD Bank	Financial & Transfers	Fees & Service Charges	10	2026-09-29 02:16:44.506513+00
\.


--
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: ledgerly
--

COPY public.transactions (transaction_id, account_id, posted_date, description, amount, merchant, category, subcategory, source, created_at) FROM stdin;
3	1	2024-12-18	121824AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
4	1	2024-12-16	121624AGILE DECISION SPAYROLL   1	0.00	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
5	1	2024-12-04	120424AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
10	1	2024-11-20	112024AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
12	1	2024-11-06	110624AGILE DECISION  DIRECT DEP1	1056.75	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
15	1	2024-10-23	102324AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
18	1	2024-10-09	100924AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
22	1	2024-09-25	092524AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
25	1	2024-09-11	091124AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
27	1	2024-08-28	082824AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
28	1	2024-08-14	081424AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
30	1	2024-07-31	073124AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
32	1	2024-07-17	071724AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
33	1	2024-07-03	070324AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
37	1	2024-06-20	062024AGILE DECISION  DIRECT DEP1	1073.62	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
39	1	2024-06-05	060524AGILE DECISION  DIRECT DEP1	1056.74	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
42	1	2024-05-22	052224AGILE DECISION  DIRECT DEP1	1051.96	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
43	1	2024-05-08	050824AGILE DECISION  DIRECT DEP1	1049.83	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
46	1	2024-04-24	042424AGILE DECISION  DIRECT DEP1	1049.83	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
50	1	2024-04-10	041024AGILE DECISION  DIRECT DEP1	1049.83	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
53	1	2024-03-27	032724AGILE DECISION  DIRECT DEP1	1049.83	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
54	1	2024-03-15	031524AGILE DECISION  DIRECT DEP1	1006.56	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
55	1	2024-03-01	030124AGILE DECISION  DIRECT DEP1	1006.55	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
57	1	2024-02-16	021624AGILE DECISION  DIRECT DEP1	1006.55	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
23	1	2024-09-18	091824SAV WITHDRAW *4800 A377031                FLAGSTAFF     *AZ	-102.50	TD Bank	Financial & Transfers	Cash & ATM	vllm_inference	2026-09-28 22:48:42.920051+00
24	1	2024-09-13	091324SAV WITHDRAW *4800 PNC BANK               BELLMAWR      *NJ	-200.00	TD Bank	Financial & Transfers	Cash & ATM	vllm_inference	2026-09-28 22:48:42.920051+00
49	1	2024-04-12	041224STATE OF N.J.   NJSTTAXRFD1	392.00	Governmant	IRS	Taxes	rule_match	2026-09-28 22:48:42.920051+00
21	1	2024-09-30	FREE ATM REBATE	2.50	TD Bank	Financial & Transfers	Cash & ATM	rule_match	2026-09-28 22:48:42.920051+00
34	1	2024-06-28	MAINTENANCE FEE	-15.00	TD Bank	Financial & Transfers	Fees & Service Charges	rule_match	2026-09-28 22:48:42.920051+00
40	1	2024-05-31	MAINTENANCE FEE	-15.00	TD Bank	Financial & Transfers	Fees & Service Charges	rule_match	2026-09-28 22:48:42.920051+00
44	1	2024-04-30	MAINTENANCE FEE	-15.00	TD Bank	Financial & Transfers	Fees & Service Charges	rule_match	2026-09-28 22:48:42.920051+00
51	1	2024-04-01	040124IRS  TREAS 310    TAX REF 2	381.00	Government	IRS	Taxes	rule_match	2026-09-28 22:48:42.920051+00
7	1	2024-12-03	WITHDRAWAL	-456.27	TD Bank	Financial & Transfers	Cash & ATM	rule_match	2026-09-28 22:48:42.920051+00
2	1	2024-12-18	Online Xfer Transfer to CK x4642	-700.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
6	1	2024-12-03	Online Xfer Transfer to CK x4642	-1000.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
9	1	2024-11-20	Online Xfer Transfer to CK x4642	-1000.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
11	1	2024-11-07	Online Xfer Transfer to CK x4642	-1000.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
14	1	2024-10-24	Online Xfer Transfer to CK x4642	-1500.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
16	1	2024-10-22	Online Xfer Transfer to CK x4642	-1000.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
17	1	2024-10-21	Online Xfer Transfer to CK x4642	-500.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
19	1	2024-10-03	Online Xfer Transfer to CK x4642	-2000.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
31	1	2024-07-18	Online Xfer Transfer to CK x4642	-1000.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
59	1	2024-02-02	020224AGILE DECISION  DIRECT DEP1	1006.55	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
61	1	2024-01-19	011924AGILE DECISION  DIRECT DEP1	1005.11	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
62	1	2024-01-05	010524AGILE DECISION  DIRECT DEP1	1007.98	AGILE DECISION	Income	Payroll & Direct Deposit	vllm_inference	2026-09-28 22:48:42.920051+00
52	1	2024-03-29	INTEREST CREDIT	45.02	TD Bank	Income	Interest	rule_match	2026-09-28 22:48:42.920051+00
56	1	2024-02-29	INTEREST CREDIT	36.12	TD Bank	Income	Interest	rule_match	2026-09-28 22:48:42.920051+00
60	1	2024-01-31	INTEREST CREDIT	36.12	TD Bank	Income	Interest	rule_match	2026-09-28 22:48:42.920051+00
38	1	2024-06-17	Online Xfer Transfer to CK x4642	-500.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
36	1	2024-06-25	Online Xfer Transfer to CK x4642	-200.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
47	1	2024-04-16	Online Xfer Transfer to CK x4642	-10000.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
48	1	2024-04-15	Online Xfer Transfer to CK x4642	-12000.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
58	1	2024-02-09	Online Xfer Transfer to CK x4642	-1000.00	TD Bank	Income	Transfer	rule_match	2026-09-28 22:48:42.920051+00
1	1	2024-12-31	INTEREST CREDIT	20.69	TD Bank	Income	Interest	rule_match	2026-09-28 22:48:42.920051+00
8	1	2024-11-29	INTEREST CREDIT	22.28	TD Bank	Income	Interest	rule_match	2026-09-28 22:48:42.920051+00
13	1	2024-10-31	INTEREST CREDIT	25.73	TD Bank	Income	Interest	rule_match	2026-09-28 22:48:42.920051+00
20	1	2024-09-30	INTEREST CREDIT	25.84	TD Bank	Income	Interest	rule_match	2026-09-28 22:48:42.920051+00
26	1	2024-08-30	INTEREST CREDIT	23.12	TD Bank	Income	Interest	rule_match	2026-09-28 22:48:42.920051+00
29	1	2024-07-31	INTEREST CREDIT	20.00	TD Bank	Income	Interest	rule_match	2026-09-28 22:48:42.920051+00
35	1	2024-06-28	INTEREST CREDIT	13.33	TD Bank	Income	Interest	rule_match	2026-09-28 22:48:42.920051+00
41	1	2024-05-31	INTEREST CREDIT	0.07	TD Bank	Income	Interest	rule_match	2026-09-28 22:48:42.920051+00
45	1	2024-04-30	INTEREST CREDIT	24.18	TD Bank	Income	Interest	rule_match	2026-09-28 22:48:42.920051+00
\.


--
-- Name: accounts_account_id_seq; Type: SEQUENCE SET; Schema: public; Owner: ledgerly
--

SELECT pg_catalog.setval('public.accounts_account_id_seq', 1, true);


--
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: ledgerly
--

SELECT pg_catalog.setval('public.categories_id_seq', 38, true);


--
-- Name: categorization_rules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: ledgerly
--

SELECT pg_catalog.setval('public.categorization_rules_id_seq', 11, true);


--
-- Name: transactions_transaction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: ledgerly
--

SELECT pg_catalog.setval('public.transactions_transaction_id_seq', 62, true);


--
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: ledgerly
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (account_id);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: ledgerly
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: categorization_rules categorization_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: ledgerly
--

ALTER TABLE ONLY public.categorization_rules
    ADD CONSTRAINT categorization_rules_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: ledgerly
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (transaction_id);


--
-- Name: accounts uq_account; Type: CONSTRAINT; Schema: public; Owner: ledgerly
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT uq_account UNIQUE (bank_name, account_type, last_four);


--
-- Name: transactions uq_account_date_amount_desc; Type: CONSTRAINT; Schema: public; Owner: ledgerly
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT uq_account_date_amount_desc UNIQUE (account_id, posted_date, amount, description);


--
-- Name: categories uq_category_subcategory; Type: CONSTRAINT; Schema: public; Owner: ledgerly
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT uq_category_subcategory UNIQUE (name, subcategory);


--
-- Name: idx_rules_priority; Type: INDEX; Schema: public; Owner: ledgerly
--

CREATE INDEX idx_rules_priority ON public.categorization_rules USING btree (priority DESC);


--
-- Name: transactions transactions_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: ledgerly
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(account_id);


--
-- PostgreSQL database dump complete
--

\unrestrict xtWAEOaQIIB8LZ5jOQjwwy01JFvvBqDo0xYZhTi8aTFGkhFeHUWRabFyOXp4Vja


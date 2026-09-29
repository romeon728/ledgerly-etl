-- ==========================================
-- RESET / CLEAN SLATE (Optional)
-- ==========================================
-- To wipe data and reset primary key auto-increment IDs:
-- TRUNCATE TABLE transactions, accounts, categorization_rules, categories RESTART IDENTITY CASCADE;

-- To completely drop all tables and start fresh:
-- DROP TABLE IF EXISTS transactions, accounts, categorization_rules, categories CASCADE;

-- ==========================================
-- SCHEMA DEFINITION
-- ==========================================

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
    account_id      SERIAL PRIMARY KEY,
    bank_name       VARCHAR(100) NOT NULL,
    account_type    VARCHAR(50) NOT NULL,
    last_four       VARCHAR(4) DEFAULT '0000',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_account
        UNIQUE (bank_name, account_type, last_four)
);

-- Category reference table
CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    
    CONSTRAINT uq_category_subcategory 
        UNIQUE (name, subcategory)
);

-- Categorization rules table
CREATE TABLE IF NOT EXISTS categorization_rules (
    id               SERIAL PRIMARY KEY,
    pattern          VARCHAR(255) NOT NULL,
    match_type       VARCHAR(20) DEFAULT 'contains', -- 'contains', 'exact', 'regex'
    target_merchant  VARCHAR(255) NOT NULL,
    target_category  VARCHAR(100) NOT NULL,
    target_subcategory VARCHAR(100),
    priority         INT DEFAULT 10,
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rules_priority ON categorization_rules(priority DESC);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id  SERIAL          PRIMARY KEY,
    account_id      INT             NOT NULL REFERENCES accounts(account_id),
    posted_date     DATE            NOT NULL,
    description     TEXT            NOT NULL,
    amount          NUMERIC(12, 2)  NOT NULL,
    merchant        VARCHAR(255),
    category        VARCHAR(100),
    subcategory     VARCHAR(100),
    source          VARCHAR(50)     DEFAULT 'vllm_inference',
    created_at      TIMESTAMP       WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_account_date_amount_desc 
        UNIQUE (account_id, posted_date, amount, description)
);

-- ==========================================
-- BASE TAXONOMY SEED DATA
-- ==========================================

INSERT INTO categories (name, subcategory) VALUES
    -- Housing
    ('Housing', 'Rent & Mortgage'),
    ('Housing', 'Other'),

    -- Transportation
    ('Transportation', 'Automotive & Fuel'),
    ('Transportation', 'Public Transit & Rideshare'),
    ('Transportation', 'Other'),

    -- Food & Dining
    ('Food & Dining', 'Groceries'),
    ('Food & Dining', 'Restaurants & Coffee'),
    ('Food & Dining', 'Other'),

    -- Shopping
    ('Shopping', 'General Retail'),
    ('Shopping', 'Other'),

    -- Utilities & Bills
    ('Utilities & Bills', 'Utilities'),
    ('Utilities & Bills', 'Subscriptions & Software'),
    ('Utilities & Bills', 'Other'),

    -- Entertainment
    ('Entertainment', 'Subscriptions & Software'),
    ('Entertainment', 'Other'),

    -- Income
    ('Income', 'Payroll & Direct Deposit'),
    ('Income', 'Other'),

    -- Financial & Transfers
    ('Financial & Transfers', 'Account Transfer'),
    ('Financial & Transfers', 'Other'),

    -- Healthcare
    ('Healthcare', 'Medical & Pharmacy'),
    ('Healthcare', 'Other'),

    -- Uncategorized
    ('Uncategorized', 'Other')
ON CONFLICT (name, subcategory) DO NOTHING;
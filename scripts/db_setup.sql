-- Accounts table (Stores user account metadata dynamically)
CREATE TABLE IF NOT EXISTS accounts (
    account_id      SERIAL PRIMARY KEY,
    bank_name       VARCHAR(100) NOT NULL,
    account_type    VARCHAR(50) NOT NULL,
    last_four       VARCHAR(4) DEFAULT '0000',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_account
        UNIQUE (bank_name, account_type, last_four)
);

-- Categorization Rules Table
CREATE TABLE IF NOT EXISTS categorization_rules (
    rule_id        SERIAL PRIMARY KEY,
    match_type     VARCHAR(20)  NOT NULL, -- 'contains', 'equals'
    match_text     VARCHAR(255) NOT NULL,
    merchant       VARCHAR(255) NOT NULL,
    category       VARCHAR(100) NOT NULL,
    subcategory    VARCHAR(100),
    active         BOOLEAN DEFAULT TRUE,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw / Enriched Transactions Table
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
-- Drop all tables before creating
DROP TABLE transactions;
DROP TABLE accounts;
DROP TABLE imports;
DROP TABLE rules;

-- Create rules table for stored merchant rules
CREATE TABLE rules (
  rule_id       SERIAL PRIMARY KEY,
  match_text    TEXT      NOT NULL,
  match_type    TEXT      NOT NULL CHECK (match_type IN ('contains', 'equals', 'regex')),
  merchant      TEXT      NOT NULL,
  category      TEXT      NOT NULL,
  subcategory   TEXT,
  is_recurring  BOOLEAN   NOT NULL DEFAULT FALSE,
  priority      INTEGER   NOT NULL DEFAULT 10,
  active        BOOLEAN   NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 1. Create imports table to track processed files
CREATE TABLE imports (
  import_id   SERIAL    PRIMARY KEY,
  filename    TEXT      NOT NULL,
  file_hash   CHAR(64)  NOT NULL,     -- SHA-256 hash of the file content
  start_date  DATE,                   -- The earliest transaction date in this file
  end_date    DATE,                   -- The latest transaction date in this file
  row_count   INTEGER,
  created_at  TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(file_hash) -- Prevents exact same file from being uploaded twice
);

-- 2. Create accounts table to store processed accounts
CREATE TABLE accounts (
  account_id      SERIAL        PRIMARY KEY,
  bank            VARCHAR(100)  NOT NULL,
  account_type    VARCHAR(50),
  account_number  VARCHAR(50),  -- Last 4

  UNIQUE (bank, account_type, account_number)
);

-- 3. Link transactions to the account and import source
CREATE TABLE transactions (
transaction_id    SERIAL          PRIMARY KEY,
  import_id       INTEGER         REFERENCES imports(import_id) ON DELETE CASCADE, -- If a log is deleted, also deletes the data
  account_id      INTEGER         NOT NULL REFERENCES accounts(account_id),
  rule_id         INTEGER         NOT NULL REFERENCES rules(rule_id),
  date            DATE            NOT NULL,
  description     TEXT,
  amount          NUMERIC(12, 2)  NOT NULL,
  merchant        VARCHAR(100),
  category        VARCHAR(50),
  subcategory     VARCHAR(50),
  is_recurring    BOOLEAN,
  flow_type       VARCHAR(10),
  created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
  sequence        INTEGER         DEFAULT 1
);

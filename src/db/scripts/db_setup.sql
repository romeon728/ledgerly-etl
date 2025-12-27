-- Create accounts table
CREATE TABLE accounts (
  account_id SERIAL PRIMARY KEY,
  bank VARCHAR(100) NOT NULL,
  account_type VARCHAR(50),
  account_number VARCHAR(50), -- Last 4

  UNIQUE (bank, account_type, account_number)
);

-- Create transactions table
CREATE TABLE transactions (
  transaction_id SERIAL PRIMARY KEY,
  account_id INTEGER NOT NULL REFERENCES accounts(account_id),
  date DATE NOT NULL,
  description TEXT,
  amount NUMERIC(12, 2) NOT NULL,
  merchant VARCHAR(100),
  category VARCHAR(50),
  subcategory VARCHAR(50),
  is_recurring BOOLEAN,
  flow_type VARCHAR(10),
  category_source VARCHAR(20),
  rule_id INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  UNIQUE (date, description, amount)
);





-- -- Create rules table
-- CREATE TABLE rules (
--   rule_id       SERIAL PRIMARY KEY,
--   match_text    TEXT NOT NULL,
--   match_type    TEXT NOT NULL CHECK (match_type IN ('contains', 'equals', 'regex')),
--   merchant      TEXT,
--   category      TEXT NOT NULL,
--   subcategory   TEXT,
--   flow_type     TEXT NOT NULL CHECK (flow_type IN ('inflow', 'outflow')),
--   priority      INTEGER NOT NULL DEFAULT 10,
--   active        BOOLEAN NOT NULL DEFAULT TRUE,
--   created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
--   updated_at    TIMESTAMP NOT NULL DEFAULT NOW()
-- );

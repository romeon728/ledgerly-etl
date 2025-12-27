# Ledgerly
Ledgerly is a self-hosted personal finance analytics tool that ingests bank statement data, normalizes and categorizes transactions, and visualizes spending trends through Grafana dashboards. It’s designed for engineers who want full control over their financial data, automation, and reporting.

Built for automation, transparency, and full ownership of your financial data.


I want to future proof this project, to do so I wanna create a ML which continues to learn from the data stored in the DB. Meaning every time I upload more data, it'll determine the merchant, category, and subcategory given the parsed data. What it's projecting is whatever becomes Unknown/Uncategoriezed after going through all of the current rules.
I want to move the rules into the database, instead of being stored in a json. Table query:

-- Create rules table
CREATE TABLE rules (
rule_id SERIAL PRIMARY KEY,
match_text TEXT NOT NULL,
match_type TEXT NOT NULL CHECK (match_type IN ('contains', 'equals', 'regex')),
merchant TEXT,
category TEXT NOT NULL,
subcategory TEXT,
flow_type TEXT NOT NULL CHECK (flow_type IN ('inflow', 'outflow')),
priority INTEGER NOT NULL DEFAULT 10,
active BOOLEAN NOT NULL DEFAULT TRUE,
created_at TIMESTAMP NOT NULL DEFAULT NOW(),
updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

I plan to implement a UI with the following:
1. A button to trigger a pipeline that parses and enriches the data
2. A button to open the current rules to add/disable/enable, which if updated will remove the enriched file and re-enrich
3. A table with the enriched data, just the header if it hasnt been parsed yet
4. A button to "upload" the data, which just adds to the database 
5. If duplicate is being processed, give warning that "proceeding will replace current information"

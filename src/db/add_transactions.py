#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import json

from database import LedgerlyDatabase

DB = LedgerlyDatabase()
TRANSACTIONS = {}

def load_transactions(path="data/enriched_transactions.json"):
  """
  Load the transactions set in path
  """
  with open(path, "r") as f:
    transactions = json.load(f)
  
  
  logging.info(f"{len(transactions['transactions'])} Transactions Loaded")
  logging.info(f"Statement Period: {transactions['statement_period']['start']} -> {transactions['statement_period']['end']}")
  logging.info(f"Account Information: {transactions['account']['bank']} | {transactions['account']['type']} x{transactions['account']['last_four']}")
  
  global TRANSACTIONS
  TRANSACTIONS = transactions
  
  return 0

def add_transactions():

  logging.info("Adding account information to database if does not exist")
  account_info = TRANSACTIONS['account']
  account_id = DB.execute(
  query="""
    INSERT INTO accounts (bank, account_type, account_number)
    VALUES (%s, %s, %s)
    ON CONFLICT (bank, account_type, account_number)
    DO UPDATE SET bank = EXCLUDED.bank
    RETURNING account_id;
  """,
  params=(account_info["bank"], account_info["type"], account_info["last_four"])
  )
  logging.info(f"Account ID: {account_id}")
  
  for tx in TRANSACTIONS["transactions"]:
    print(tx)
    print(tx.values())
    tx_tuple = tuple([account_id] + list(tx.values()))
    DB.execute(
    query="""
      INSERT INTO transactions (account_id, date, description, amount, merchant,
        category, subcategory, is_recurring, flow_type, category_source, rule_id)
      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
      ON CONFLICT DO NOTHING;
    """,
    params=tx_tuple
    )

  logging.info("Committing changes and closing database")
  DB.commit()
  DB.close()
  return

# ----------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------
if __name__ == "__main__":
  # Configure logging
  logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

  DB.connect()
  load_transactions()
  add_transactions()
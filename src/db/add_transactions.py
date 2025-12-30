#!/usr/bin/env python3

import logging
import json
from collections import Counter

from agents.database import LedgerlyDatabase

DB = LedgerlyDatabase()
TRANSACTIONS = {}

def load_transactions(path="data/enriched_transactions.json"):
  """
  Load the transactions set in path
  """
  with open(path, "r") as f:
    transactions = json.load(f)
  
  
  logging.info(f"{len(transactions['transactions'])} Transactions Loaded")
  logging.info(f"\tStatement Period: {transactions['statement_period']['start']} -> {transactions['statement_period']['end']}")
  logging.info(f"\tAccount Information: {transactions['account']['bank']} | {transactions['account']['type']} x{transactions['account']['last_four']}")
  
  global TRANSACTIONS
  TRANSACTIONS = transactions
  
  return 0

def add_import():
  """
  Docstring for add_import
  """ 

  import_info = TRANSACTIONS["import_info"]
  statement_period = TRANSACTIONS["statement_period"]
  # Check if hash is already being stored in the database
  if DB.fetchone(
      query="SELECT 1 FROM imports WHERE file_hash = %s;",
      params=(import_info["file_hash"],)
    ):
    logging.info("Duplicate File: This file has already been processed")
    exit(1)

  # Insert import, since hash does not exist in DB yet
  import_id = DB.execute(
    query="""
      INSERT INTO imports (filename, file_hash, start_date, end_date, row_count)
      VALUES (%s, %s, %s, %s, %s)
      RETURNING import_id;
    """,
    params=(import_info["filename"], import_info["file_hash"], statement_period["start"], statement_period["end"], import_info["row_count"])
  )

  logging.info("New import successfully added to DB")

  return import_id

def add_transactions(import_id:int):

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
  
  num_tx_added = 0
  counts = Counter()
  for tx in TRANSACTIONS["transactions"]:
    if not isinstance(tx, dict):
      logging.error(f"Transaction is not expected dictionary: {tx}")
      exit(1)

    key = (tx.get("date"), tx.get("description"), tx.get("amount"), tx.get("merchant"), tx.get("category"))
    counts[key] += 1
    seq = counts[key]


    exists = DB.fetchone(
      query="""
        SELECT 1 FROM transactions 
        WHERE account_id = %s AND rule_id = %s AND date = %s AND description = %s AND amount = %s AND sequence = %s
      """,
      params=(account_id, tx.get("rule_id"), tx.get("date"), tx.get("description"), tx.get("amount"), seq)
    )
    
    if not exists:
      DB.execute(
        query="""
          INSERT INTO transactions (account_id, import_id, rule_id, date, description, amount, 
            merchant, category, subcategory, is_recurring, flow_type, sequence)
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        params=(
          account_id, import_id, tx.get("rule_id"), tx.get("date"), tx.get("description"), tx.get("amount"), tx.get("merchant"), 
          tx.get("category"), tx.get("subcategory"), tx.get("is_recurring"), tx.get("flow_type"), seq 
        )
      )
      num_tx_added += 1
    else:
      logging.warning(f"Skipping Duplicate Row: {key}")
  
  logging.info(f"{num_tx_added} transactions added to DB")

  return 0

# ----------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------
if __name__ == "__main__":
  # Configure logging
  logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

  # Connect to Database
  DB.connect()

  # Load Transactions
  load_transactions()

  # Add the import and transactions to DB
  import_id = add_import()
  add_transactions(import_id)

  logging.info("Committing changes and closing database")
  DB.commit()
  DB.close()
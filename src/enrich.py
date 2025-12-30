#!/usr/bin/env python3

import logging
import json
from pathlib import Path
import os

from db.agents.database import LedgerlyDatabase

"""
Cleans the transactions 
"""

DB = LedgerlyDatabase()

RULES = []
TRANSACTIONS = {}

def load_rules(path="rules/merchant_rules.json"):
  """
  Load the rules set in path
  """

  rules = DB.fetchall(
    query="SELECT * FROM rules ORDER BY priority DESC;"
  )
  logging.info(f"{len(rules)} Rules Loaded")
  global RULES
  RULES = rules
  
  return 0

def load_transactions(path="data/transaction_data.json"):
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

def enrich_transaction(tx:dict):
  """
  Entrypoint for enriching transactions.
  """
  
  def unkown_description(rule:dict, description:str):
    if rule.get("merchant") == "Unknown" and rule.get("category") == "Uncategorized":
      logging.warning(f"Unknown Description: {description}")
      return True
    return False
  
  def matches(rule:dict, description:str):
    desc = description.upper()
    pattern = rule.get("match_text").upper()

    if rule.get("match_type") == "contains" or rule.get("match_type") == "equals":
      if pattern in desc or pattern == desc: 
        logging.info(f"Matched: {desc} -> {pattern}")
        return True
    return False

  description = tx.get("description")
  for rule in RULES:
    # Skip inactive rules
    if not rule.get("active", True):
      continue
    
    # Enrich transaction
    # Check if description equals/contains the pattern
    # If Unknown (last rule in the list), set to uncategorized
    if matches(rule, description) or unkown_description(rule, description):
      tx["merchant"] = rule.get("merchant")
      tx["category"] = rule.get("category")
      tx["subcategory"] = rule.get("subcategory") or rule.get("category")
      tx["is_recurring"] = rule.get("is_recurring")
      tx["flow_type"] = "inflow" if tx["amount"] > 0 else "outflow"
      tx["rule_id"] = rule.get("rule_id")

      return tx
    
    else:
      continue

  logging.error("INVESTIGATE WHY IT GOT THIS FAR")
  exit(1)


def enrich_transactions():
  logging.info("Starting transaction enrichment...")
  transactions = TRANSACTIONS["transactions"]
  enriched_transactions = [enrich_transaction(tx) for tx in transactions]

  enriched_data = {
    "import_info": TRANSACTIONS.get("import_info"),
    "statement_period": TRANSACTIONS.get("statement_period"),
    "account": TRANSACTIONS.get("account"),
    "transactions": enriched_transactions
  }

  logging.info("Finished transaction enrichment.")

  # Save enriched transactions back to file
  file_path = "./data/enriched_transactions.json"
  logging.info(f"Dumping enriched transactions into JSON: {file_path}")

  directory = os.path.dirname(file_path)
  if not os.path.exists(directory):
    os.makedirs(directory)

  with open(file_path, 'w') as json_file:
    json.dump(enriched_data, json_file, indent=4)

  return 0


# ----------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------
if __name__ == "__main__":
  # Configure logging
  logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
  
  DB.connect()

  load_rules()
  load_transactions()
  enrich_transactions()

  DB.commit()
  DB.close()
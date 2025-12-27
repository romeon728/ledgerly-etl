#!/usr/bin/env python3

import logging
import json
from pathlib import Path
import os

"""
Cleans the transactions 
"""

RULES = []
TRANSACTIONS = {}

def load_rules(path="rules/merchant_rules.json"):
  """
  Load the rules set in path
  """
  with open(path, "r") as f:
    rules = json.load(f)
  
  logging.info(f"{len(rules)} Rules Loaded")
  if len(rules) != rules[-1]['id']:
    logging.error("Last ID does not match number of rules in merchange_rules.json; Exiting...")
    exit(1)

  rules.sort(key=lambda r: r.get("priority", 10), reverse=True)

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
  logging.info(f"Statement Period: {transactions['statement_period']['start']} -> {transactions['statement_period']['end']}")
  logging.info(f"Account Information: {transactions['account']['bank']} | {transactions['account']['type']} x{transactions['account']['last_four']}")
  
  global TRANSACTIONS
  TRANSACTIONS = transactions
  
  return 0

def enrich_transaction(tx:dict):
  """
  Entrypoint for enriching transactions.
  """
  
  def matches(rule:dict, description:str):
    desc = description.upper()
    pattern = rule["match"].upper()
    # print(f"{desc} -> {pattern}")

    if rule["match_type"] == "contains":
      return pattern in desc
    elif rule["match_type"] == "equals":
      return pattern == desc
    # Extend with regex or other types as needed
    return False

  description = tx.get("description")
  matched = False
  for rule in RULES:
    # Skip inactive rules
    if not rule.get("active", True):
      continue
    
    if matches(rule, description):
      # Enrich transaction
      tx["merchant"] = rule.get("merchant")
      tx["category"] = rule.get("category")
      tx["subcategory"] = rule.get("subcategory") or rule.get("category")
      tx["is_recurring"] = rule.get("is_recurring")
      tx["flow_type"] = rule.get("flow_type") or ("inflow" if tx["amount"] > 0 else "outflow")
      tx["category_source"] = "rule"
      tx["rule_id"] = rule.get("id")
      
      matched = True
    
    else:
      continue
    
    if matched:
      logging.info(f"Matched: {description} -> {rule.get("match")}")
      return tx

  # No rule matched
  logging.warning(f"Unknown Description: {description}")
  tx["merchant"] = tx.get("merchant") or "Unknown"
  tx["category"] = tx.get("category") or "Uncategorized"
  tx["subcategory"] = tx.get("subcategory") or tx["category"]
  tx["is_recurring"] = tx.get("is_recurring")
  tx["flow_type"] = "inflow" if tx["amount"] > 0 else "outflow"
  tx["category_source"] = "unmatched"
  tx["rule_id"] = None
  return tx


def enrich_transactions():
  logging.info("Starting transaction enrichment...")
  transactions = TRANSACTIONS["transactions"]
  enriched_transactions = [enrich_transaction(tx) for tx in transactions]

  enriched_data = {
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

  load_rules()
  load_transactions()
  enrich_transactions()
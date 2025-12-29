#!/usr/bin/env python3

import logging
import json

from agents.database import LedgerlyDatabase

DB = LedgerlyDatabase()
RULES = {}

def load_rules(path="rules/merchant_rules.json"):
  """
  Load the transactions set in path
  """
  with open(path, "r") as f:
    rules = json.load(f)
  
  
  logging.info(f"{len(rules)} Rules Loaded")
  
  global RULES
  RULES = rules
  
  return 0

def add_rules_json_to_db():

  rules_added = 0
  for rule in RULES:
    key = tuple(list(rule.values())[1:5])
    exists = DB.fetchone(
      query="""
        SELECT 1 FROM rules 
        WHERE match_text = %s AND match_type = %s AND merchant = %s AND category = %s
      """,
      params=key
    )
    
    if not exists:
      rules_to_import = tuple(list(rule.values())[1:])
      DB.execute(
        query="""
          INSERT INTO rules (match_text, match_type, merchant, category, 
            subcategory, is_recurring, priority, active)
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        params=rules_to_import
      )
      rules_added += 1

  logging.info(f"{rules_added} Rules Added to DB")
  return

# ----------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------
if __name__ == "__main__":
  # Configure logging
  logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

  DB.connect()

  # Load Rules
  load_rules()

  # Add the rules found in merchant_rules.json to DB
  add_rules_json_to_db()

  logging.info("Committing changes and closing database")
  DB.commit()
  DB.close()
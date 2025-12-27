#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor
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

def add_rules():
	
	logging.info("THIS IS TBD")
	
	DB.close()
	return

# ----------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------
if __name__ == "__main__":
  # Configure logging
  logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

  DB.connect()
  load_rules()
  add_rules()
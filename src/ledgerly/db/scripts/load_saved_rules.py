
import json
import os


from src.ledgerly.agents.database import LedgerlyDatabase
from src.ledgerly.db.sessions import ImportManager, RulesEngine, AccountTransactions

"""
Docstring for ledgerly.db.scripts.load_saved_rules

This script is ran to load the rules that are saved to ledgerly.ml.data.merchant_rules.json

When to run: When the tables are dropped and re-created
"""



def main():
  
  # 1. Load rules from JSON
  script_path = os.path.abspath(__file__)
  print(script_path)
  


if __name__ == "__main__":
  main()
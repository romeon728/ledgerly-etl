import pandas as pd
import math
import os
import json

import logging
from agents.logger_config import setup_logging
log_buffer = setup_logging()
logger = logging.getLogger("ledgerly")
from agents.database import LedgerlyDatabase

import db.queries as queries

"""
Docstring for ledgerly.db.sessions

Contains the sessions used during the business logic for:
- imports
- rules
- transactions
"""

##################################################
# IMPORT SESSION
##################################################

class ImportManager():

  def __init__(self):
    logger.info("ImportManager (Class): Initialized")

  def get_imports(self, db:LedgerlyDatabase):
    self.current_imports = None
    self.current_imports_df = None
    self.current_imports, self.current_imports_df = queries.get_imports(db)
    logger.info(f"{len(self.current_imports)} imports loaded")

  def delete_imports(self, db:LedgerlyDatabase, imports_to_del:pd.DataFrame):
    logger.info(f"Deleting the following {len(imports_to_del)} imports:\n{imports_to_del}")
    queries.delete_imports(db, imports_to_del)
  
  def add_import(self, db:LedgerlyDatabase, enriched_transactions:dict):
    self.import_id = queries.add_import(db, enriched_transactions)
    logger.info("New import successfully added to DB")
    logger.info(f"Import ID: {self.import_id}")
    self.get_imports(db)


##################################################
# RULES SESSION
##################################################

class RulesEngine():

  def __init__(self):
    logger.info("MerchangeRules (Class): Initialized")

  def load_rules(self, db:LedgerlyDatabase):
    self.rules = queries.load_rules(db)

  def add_rule(self, db:LedgerlyDatabase, rules_data:list):
    self.matched_descriptions_rules, self.already_exists_rules = \
      queries.add_rule(db, rules_data)

  def update_rules(self, db:LedgerlyDatabase, rules_df:pd.DataFrame):
    queries.update_rules(db, rules_df)

  def tuple_is_valid(self, t:tuple, indexes:list):
    def is_valid(value):
      if value is None:
        return False
      if value == "":
        return False
      if isinstance(value, float) and math.isnan(value):
        return False
      return True
    return all(is_valid(t[i]) for i in indexes)

  def add_unknown_rule(self, db:LedgerlyDatabase):
    unknown_rule = [("Unknown", "contains", "Unknown", "Uncategorized", "Uncategorized", False, 0)]
    self.add_rule(db, unknown_rule)
    self.load_rules(db)
  
  def populate_json_rules(self, db:LedgerlyDatabase):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    rules_json = f"{current_dir}/../ml/data/merchant_rules.json"
    rules_to_add = []
    with open(rules_json, 'r') as f:
      rules_data = list(json.load(f))[1:]
      for rule in rules_data:
        rules_to_add.append(tuple(list(dict(rule).values())[1:-1]))
    self.add_rule(db, rules_to_add)
    self.load_rules(db)

##################################################
# TRANSACTIONS SESSION
##################################################

class AccountTransactions():

  def __init__(self):
    logger.info("AccountTransactions (Class): Initialized")

  def add_transactions(self, db:LedgerlyDatabase, import_id:int, enriched_transactions:dict):
    self.num_tx_added = queries.add_transactions(db, import_id, enriched_transactions)

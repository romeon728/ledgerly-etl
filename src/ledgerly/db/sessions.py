import pandas as pd
import math

import logging
from agents.logger_config import setup_logging
log_buffer = setup_logging()
logger = logging.getLogger("ledgerly")
from agents.database import LedgerlyDatabase

import db.queries as queries
import parser
import enrich

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
    queries.add_import(db, enriched_transactions)
    self.import_id = logger.info("New import successfully added to DB")
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


##################################################
# TRANSACTIONS SESSION
##################################################

class AccountTransactions():

  def __init__(self):
    logger.info("AccountTransactions (Class): Initialized")

  # --------------------------------------------------
  # STREAMLIT PIPELINE FUNCTIONS
  # --------------------------------------------------

  def process_transactions(self, uploaded_file, db:LedgerlyDatabase, re:RulesEngine):
    # Parse and enrich transactions
    self.parsed_transactions = parser.parse_csv(uploaded_file)
    self.enriched_transactions = enrich.enrich_parsed_transactions(self.parsed_transactions, db, re)

    # Convert transactions into DataFrame
    self.enriched_transactions_df = pd.DataFrame(list(self.enriched_transactions["transactions"]))
    self.enriched_transactions_df['date'] = pd.to_datetime(self.enriched_transactions_df['date']).dt.date

    # Extract unknown transactions into DataFrame
    self.unknown_transactions_df = self.enriched_transactions_df[
      (self.enriched_transactions_df["merchant"] == "Unknown") & 
      (self.enriched_transactions_df["category"] == "Uncategorized")
    ]
    self.unknown_transactions_df = self.unknown_transactions_df.reset_index(drop=True)

    return 0
  
  # --------------------------------------------------
  # CONSOLE PIPELINE FUNCTIONS
  # --------------------------------------------------
  
  def add_transactions(self, db:LedgerlyDatabase, import_id:int):
    self.num_tx_added = queries.add_transactions(db, import_id, self.enriched_transactions)

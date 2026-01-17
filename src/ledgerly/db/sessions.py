import pandas as pd
import json
import math
from collections import Counter

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
    db.connect()

    import_info = enriched_transactions["import_info"]
    statement_period = enriched_transactions["statement_period"]
    # Check if hash is already being stored in the database
    if db.fetchone(
        query="SELECT 1 FROM imports WHERE file_hash = %s;",
        params=(import_info["file_hash"],)
      ):
      logger.info("Duplicate File: This file has already been processed")
      return 0

    # Insert import, since hash does not exist in DB yet
    import_id = db.execute(
      query="""
        INSERT INTO imports (filename, file_hash, start_date, end_date, row_count)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING import_id;
      """,
      params=(import_info["filename"], import_info["file_hash"], statement_period["start"], statement_period["end"], import_info["row_count"])
    )

    db.commit()
    db.close()

    logger.info("New import successfully added to DB")
    logger.info(f"Import ID: {import_id}")

    # Update self.current_imports
    self.get_imports(db)

    return import_id


##################################################
# RULES SESSION
##################################################

class RulesEngine():

  def __init__(self):
    logger.info("MerchangeRules (Class): Initialized")

  # --------------------------------------------------
  # STREAMLIT PIPELINE FUNCTIONS
  # --------------------------------------------------

  def load_rules(self, db:LedgerlyDatabase):
    """
    Loads the rules from the database
    
    :param db: Instance of Database
    :type db: LedgerlyDatabase
    """
    db.connect()
    self.rules = db.fetchall(
      query="""
        SELECT 
          rule_id,
          match_text,
          match_type,
          merchant,
          category,
          subcategory,
          is_recurring,
          priority,
          active
        FROM rules
        ORDER BY priority DESC, match_text, merchant;
      """
    )
    logger.info(f"{len(self.rules)} Rules Loaded")
    
    db.close()

  def add_rule(self, db:LedgerlyDatabase, rules_data:list):
    """
    Adds the rules given in the rules_df to the database
    
    :param db: Instance of Database
    :type db: LedgerlyDatabase
    :param rules_data: List of tuples of the rules being added
    :type rules_data: list
    """
    self.matched_descriptions_rules = []
    self.already_exists_rules = []
    db.connect()

    for rule in rules_data:
      rule = tuple(list(rule) + [True])
      if not self._exists(db, rule):
        if not self._match_text_exists(db, rule):
          logger.info(f"Adding Rule: {rule}")
          db.execute(
            query="""
              INSERT INTO rules (match_text, match_type, merchant, category, 
                subcategory, is_recurring, priority, active)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            params=rule
          )
        else:
          logger.warning(f"Adding rule with description that already exists!!! Description Text: {rule[0]}")
          self.matched_descriptions_rules.append(rule)
      else:
        logger.info(f"Skipping upload, rule already exists: {rule}")
        self.already_exists_rules.append(rule)
    
    db.commit()
    db.close()

  def update_rules(self, db:LedgerlyDatabase, rules_df:pd.DataFrame):
    """
    Updates the rules given in the rules_df for the database.
    
    NOTE: rules_df should only contain rules that already exist within db.
    
    :param db: Instance of Database
    :type db: LedgerlyDatabase
    :param rules_df: Pandas DataFrame of the rules being updated
    :type rules_df: pd.DataFrame
    """
    db.connect()
    rules_tuples = list(rules_df.itertuples(index=False, name=None))

    for rule in rules_tuples:
      if self._exists(db, rule):
        logger.info(f"Updating Rule: {rule}")
        # db.execute(
        #   query="""
        #     INSERT INTO rules (match_text, match_type, merchant, category, 
        #       subcategory, is_recurring, priority, active)
        #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        #   """,
        #   params=rule
        # )
      else:
        logger.info(f"Skipping update, A rule that doesnt exist cant be updated: {rule}")
    
    db.commit()
    db.close()

  def _exists(self, db:LedgerlyDatabase, rule:tuple):
    """
    Helper function to check if rule exists 
    
    :param db: Instance of Database
    :type db: LedgerlyDatabase
    :param rules_df: Pandas DataFrame of the rules being updated
    :type rules_df: pd.DataFrame
    """
    # key = tuple(list(rule)[1:5])
    key = rule[1:5]
    exists = db.fetchone(
      query="""
        SELECT 1 FROM rules 
        WHERE match_text = %s AND match_type = %s AND merchant = %s AND category = %s
      """,
      params=key
    )
    return exists
  
  def _match_text_exists(self, db:LedgerlyDatabase, rule:tuple):
    """
    Helper function to check if description exists 
    
    :param db: Instance of Database
    :type db: LedgerlyDatabase
    :param rules_df: Pandas DataFrame of the rules being updated
    :type rules_df: pd.DataFrame
    """
    exists = db.fetchone(
      query="""
        SELECT 1 FROM rules 
        WHERE match_text = %s
      """,
      params=(rule[0],)
    )
    return exists
  
  # --------------------------------------------------
  # CONSOLE PIPELINE FUNCTIONS
  # --------------------------------------------------

  # --- DEPRECATED ---
  def _load_json_rules(self, path="rules/merchant_rules.json"):
    """
    Load the transactions set in path

    Stores self.json_rules

    Returns status
    """
    with open(path, "r") as f:
      self.json_rules = list(json.load(f))

    if len(self.json_rules) != self.json_rules[-1]['id']:
      logger.error("Last ID does not match number of rules in merchange_rules.json; Exiting...")
      exit(1)

    self.json_rules.sort(key=lambda r: r.get("priority", 10), reverse=True)
    logger.info(f"{len(self.json_rules)} Rules Loaded")
    return 0


  # --- DEPRECATED ---
  def _add_json_rules_to_db(self, db:LedgerlyDatabase):
    """
    Adds the rules json to the database

    Returns status
    """
    db.connect()
    rules_added = 0
    for rule in self.json_rules:
      if not isinstance(rule, dict):
        logger.error(f"Rule is not a dictionary: {rule}")
        exit(1)

      key = tuple(list(rule.values())[1:5])
      exists = db.fetchone(
        query="""
          SELECT 1 FROM rules 
          WHERE match_text = %s AND match_type = %s AND merchant = %s AND category = %s
        """,
        params=key
      )
      
      if not exists:
        rules_to_import = tuple(list(rule.values())[1:])
        db.execute(
          query="""
            INSERT INTO rules (match_text, match_type, merchant, category, 
              subcategory, is_recurring, priority, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
          """,
          params=rules_to_import
        )
        rules_added += 1

    logger.info(f"{rules_added} Rules Added to DB")

    db.commit()
    db.close()

    return 0


  # --------------------------------------------------
  # HELPER FUNCTIONS
  # --------------------------------------------------

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

    db.connect()

    logger.info("Adding account information to database if does not exist")
    account_info = self.enriched_transactions['account']
    account_id = db.execute(
      query="""
        INSERT INTO accounts (bank, account_type, account_number)
        VALUES (%s, %s, %s)
        ON CONFLICT (bank, account_type, account_number)
        DO UPDATE SET bank = EXCLUDED.bank
        RETURNING account_id;
      """,
      params=(account_info["bank"], account_info["type"], account_info["last_four"])
    )
    logger.info(f"Account ID: {account_id}")
    
    self.num_tx_added = 0
    counts = Counter()
    for tx in self.enriched_transactions["transactions"]:
      if not isinstance(tx, dict):
        logger.error(f"Transaction is not expected dictionary: {tx}")
        db.close()
        return 0

      key = (tx.get("date"), tx.get("description"), tx.get("amount"), tx.get("merchant"), tx.get("category"))
      counts[key] += 1
      seq = counts[key]


      exists = db.fetchone(
        query="""
          SELECT 1 FROM transactions 
          WHERE account_id = %s AND rule_id = %s AND date = %s AND description = %s AND amount = %s AND sequence = %s
        """,
        params=(account_id, tx.get("rule_id"), tx.get("date"), tx.get("description"), tx.get("amount"), seq)
      )
      
      if not exists:
        db.execute(
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
        self.num_tx_added += 1
      else:
        logger.warning(f"Skipping Duplicate Row: {key}")
    
    logger.info(f"{self.num_tx_added} transactions added to DB")

    db.commit()
    db.close()

    return self.num_tx_added


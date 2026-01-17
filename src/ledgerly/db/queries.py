import pandas as pd
from collections import Counter

import logging
from agents.logger_config import setup_logging
log_buffer = setup_logging()
logger = logging.getLogger("ledgerly")
from agents.database import LedgerlyDatabase
"""

Docstring for ledgerly.db.queries

Contains the queries used inside of the sessions for:
- imports
- rules
- transactions
"""

##################################################
# HELPER FUNCTIONS
##################################################

def rule_exists(db:LedgerlyDatabase, rule:tuple):
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

def rule_match_text_exists(db:LedgerlyDatabase, rule:tuple):
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


##################################################
# IMPORT SESSION
##################################################

def get_imports(db:LedgerlyDatabase):
  db.connect()
  current_imports = db.fetchall(
    query="""
      SELECT 
        FALSE AS is_selected,
        a.bank,
        i.filename,
        i.start_date,
        i.end_date,
        i.row_count,
        a.account_type,
        a.account_number
      FROM imports AS i
      JOIN transactions AS t ON i.import_id = t.import_id
      JOIN accounts AS a ON t.account_id = a.account_id
      GROUP BY 
        a.bank,
        i.filename,
        i.start_date,
        i.end_date,
        i.row_count,
        a.account_type,
        a.account_number
      ORDER BY a.bank, i.start_date, a.account_type;
    """
  )
  db.close()
  return (current_imports, pd.DataFrame(current_imports))

def delete_imports(db:LedgerlyDatabase, imports_to_del:pd.DataFrame):
  db.connect()
  imports_to_del_list = list(imports_to_del.itertuples(index=False, name=None))
  for i in imports_to_del_list:
    params = tuple(list(i)[1:])
    logger.debug(f"Import Params for File Hash (fetchone): {params}")

    file_hash = db.fetchone(
      query="""
        SELECT i.file_hash
        FROM imports AS i
        JOIN transactions AS t ON i.import_id = t.import_id
        JOIN accounts AS a ON t.account_id = a.account_id
        WHERE a.bank = %s
          AND i.filename = %s
          AND i.start_date = %s
          AND i.end_date = %s
          AND i.row_count = %s
          AND a.account_type = %s
          AND a.account_number = %s
      """,
      params=params
    )['file_hash']
    logger.info(f"Deleting file hash: {file_hash}")
    
    db.execute(
      query="""
        DELETE FROM imports WHERE file_hash = %s
      """,
      params=(file_hash,)
    )
  
  db.commit()
  db.close()

def add_import(db:LedgerlyDatabase, enriched_transactions:dict):
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

  return import_id

##################################################
# RULES SESSION
##################################################

def load_rules(db:LedgerlyDatabase):
  """
  Loads the rules from the database
  
  :param db: Instance of Database
  :type db: LedgerlyDatabase
  """
  db.connect()
  rules = db.fetchall(
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
  logger.info(f"{len(rules)} Rules Loaded")
  
  db.close()
  return rules

def add_rule(db:LedgerlyDatabase, rules_data:list):
  """
  Adds the rules given in the rules_df to the database
  
  :param db: Instance of Database
  :type db: LedgerlyDatabase
  :param rules_data: List of tuples of the rules being added
  :type rules_data: list
  """
  matched_descriptions_rules = []
  already_exists_rules = []
  db.connect()
  for rule in rules_data:
    rule = tuple(list(rule) + [True])
    if not rule_exists(db, rule):
      if not rule_match_text_exists(db, rule):
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
        matched_descriptions_rules.append(rule)
    else:
      logger.info(f"Skipping upload, rule already exists: {rule}")
      already_exists_rules.append(rule)
  
  db.commit()
  db.close()
  return matched_descriptions_rules, already_exists_rules

def update_rules(db:LedgerlyDatabase, rules_df:pd.DataFrame):
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
    if rule_exists(db, rule):
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

##################################################
# TRANSACTIONS SESSION
##################################################

def add_transactions(db:LedgerlyDatabase, import_id:int, enriched_transactions:dict):

  db.connect()

  logger.info("Adding account information to database if does not exist")
  account_info = enriched_transactions['account']
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
  
  num_tx_added = 0
  counts = Counter()
  for tx in enriched_transactions["transactions"]:
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
      num_tx_added += 1
    else:
      logger.warning(f"Skipping Duplicate Row: {key}")
  
  logger.info(f"{num_tx_added} transactions added to DB")

  db.commit()
  db.close()

  return num_tx_added

#!/usr/bin/env python3
import pandas as pd
from collections import Counter
from datetime import date

import logging
from logger_config import setup_logging

log_buffer = setup_logging()
logger = logging.getLogger("ledgerly")

from db.agents.database import LedgerlyDatabase

class AccountTransactions():

  def __init__(self):
    logger.info("MerchangeRules (Class): Initialized")

  # --------------------------------------------------
  # STREAMLIT PIPELINE FUNCTIONS
  # --------------------------------------------------

  def process_transactions_df(self, enriched_transactions) -> pd.DataFrame:
    self.enriched_transactions_df = pd.DataFrame(list(enriched_transactions["transactions"]))
    self.enriched_transactions_df['date'] = pd.to_datetime(self.enriched_transactions_df['date']).dt.date
    return self.enriched_transactions_df

  # --------------------------------------------------
  # CONSOLE PIPELINE FUNCTIONS
  # --------------------------------------------------
  
  def add_import(self, db:LedgerlyDatabase, enriched_transactions:dict):
    """
    Docstring for add_import
    """ 

    db.connect()

    import_info = enriched_transactions["import_info"]
    statement_period = enriched_transactions["statement_period"]
    # Check if hash is already being stored in the database
    if db.fetchone(
        query="SELECT 1 FROM imports WHERE file_hash = %s;",
        params=(import_info["file_hash"],)
      ):
      logger.info("Duplicate File: This file has already been processed")
      exit(1)

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

    return import_id

  def add_transactions(self, db:LedgerlyDatabase, import_id:int, enriched_transactions:dict):

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
        exit(1)

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

    return 0

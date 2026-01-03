#!/usr/bin/env python3
import pandas as pd
from collections import Counter
from datetime import date

import logging
from logger_config import setup_logging

log_buffer = setup_logging()
logger = logging.getLogger("ledgerly")

from db.agents.database import LedgerlyDatabase
from db.rules import RulesEngine
import parser
import enrich

class AccountTransactions():

  def __init__(self):
    logger.info("AccountTransactions (Class): Initialized")

  # --------------------------------------------------
  # STREAMLIT PIPELINE FUNCTIONS
  # --------------------------------------------------

  def process_transactions(self, uploaded_file, re:RulesEngine) -> pd.DataFrame:
    # Parse and enrich transactions
    self.parsed_transactions = parser.parse_csv(uploaded_file)
    self.enriched_transactions = enrich.enrich_parsed_transactions(self.parsed_transactions, re)

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

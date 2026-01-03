#!/usr/bin/env python3

import json

import logging
from logger_config import setup_logging

log_buffer = setup_logging()
logger = logging.getLogger("ledgerly")

from db.agents.database import LedgerlyDatabase

class RulesEngine():

  def __init__(self):
    logger.info("MerchangeRules (Class): Initialized")

  # --------------------------------------------------
  # STREAMLIT PIPELINE FUNCTIONS
  # --------------------------------------------------

  def load_rules(self, db:LedgerlyDatabase):
    """
    Gets the rules from the database

    Stores in self.rules

    Returns status
    """

    db.connect()

    self.rules = db.fetchall(
      query="SELECT * FROM rules ORDER BY priority DESC, active;"
    )
    logger.info(f"{len(self.rules)} Rules Loaded")
    
    db.close()
    return 0


  # --------------------------------------------------
  # CONSOLE PIPELINE FUNCTIONS
  # --------------------------------------------------

  def load_json_rules(self, path="rules/merchant_rules.json"):
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

  def add_json_rules_to_db(self, db:LedgerlyDatabase):
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


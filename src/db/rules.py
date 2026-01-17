#!/usr/bin/env python3

import json
import pandas as pd
import math

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
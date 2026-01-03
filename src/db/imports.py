#!/usr/bin/env python3

import logging
from logger_config import setup_logging

log_buffer = setup_logging()
logger = logging.getLogger("ledgerly")

from db.agents.database import LedgerlyDatabase

class ImportManager():

  def __init__(self):
    logger.info("ImportManager (Class): Initialized")

  # --------------------------------------------------
  # STREAMLIT PIPELINE FUNCTIONS
  # --------------------------------------------------

  def get_imports(db:LedgerlyDatabase):
    """
    Docstring for get_imports
    
    :param db: Description
    :type db: LedgerlyDatabase
    """
    
    db.connect()
    
  
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

    return import_id

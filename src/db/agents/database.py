#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor
import logging

class LedgerlyDatabase:

  DBNAME = "ledgerly_db"
  USER = "nromeo"
  
  def __init__(self):
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    self.conn = None
    logging.info("Ledgerly Database (Class): Initialized")

  def connect(self):
    try:
      if self.conn is None:
        self.conn = psycopg2.connect(
          dbname=self.DBNAME,
          user=self.USER,
          host=""
        )
    except Exception as err:
      logging.error(f"Failed to Connect to Legderly Database: {err}")
    logging.info("Ledgerly Database: Connected")
  
  def execute(self, query:str, params:tuple=None):
    with self.conn.cursor() as cur:
      cur.execute(query, params)

      # If the query has a RETURNING clause
      if cur.description is not None:
        return cur.fetchone()[0]

      return None
  
  def fetchone(self, query:str, params:tuple=None):
    with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
      cur.execute(query, params)
      return cur.fetchone()
    
  def fetchall(self, query:str, params:tuple=None):
    with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
      cur.execute(query, params)
      return cur.fetchall()

  def commit(self):
    self.conn.commit()
    logging.info("Ledgerly Database (Changes): Committed")

  def close(self):
    if self.conn:
      self.conn.close()
      self.conn = None
    logging.info("Ledgerly Database: Closed")

#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor

import logging
logger = logging.getLogger(__name__)

class LedgerlyDatabase:

  DBNAME = "ledgerly_db"
  USER = "nromeo"
  
  def __init__(self):
    self.conn = None
    logger.info("Ledgerly Database (Class): Initialized")

  def connect(self):
    try:
      if self.conn is None:
        self.conn = psycopg2.connect(
          dbname=self.DBNAME,
          user=self.USER,
          host=""
        )
    except Exception as err:
      logger.error(f"Failed to Connect to Legderly Database: {err}")
    logger.info("Ledgerly Database: Connected")
  
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
      res = cur.fetchone()
      return dict(res) if res else None    
    
  def fetchall(self, query:str, params:tuple=None):
    with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
      cur.execute(query, params)
      return [dict(row) for row in cur.fetchall()]

  def commit(self):
    self.conn.commit()
    logger.info("Ledgerly Database (Changes): Committed")

  def close(self):
    if self.conn:
      self.conn.close()
      self.conn = None
    logger.info("Ledgerly Database: Closed")

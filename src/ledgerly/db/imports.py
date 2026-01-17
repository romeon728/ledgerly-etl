import pandas as pd
import logging
from agents.logger_config import setup_logging
log_buffer = setup_logging()
logger = logging.getLogger("ledgerly")
from agents.database import LedgerlyDatabase

class ImportManager():

  def __init__(self):
    logger.info("ImportManager (Class): Initialized")

  # --------------------------------------------------
  # STREAMLIT PIPELINE FUNCTIONS
  # --------------------------------------------------

  def get_imports(self, db:LedgerlyDatabase):
    """
    Docstring for get_imports
    
    :param db: Description
    :type db: LedgerlyDatabase
    """
    
    db.connect()
    self.current_imports = None
    self.current_imports_df = None
    self.current_imports = db.fetchall(
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
    self.current_imports_df = pd.DataFrame(self.current_imports)
    return 0

  def delete_imports(self, db:LedgerlyDatabase, imports_to_del:pd.DataFrame):
    db.connect()
    logger.info(f"Deleting the following {len(imports_to_del)} imports:\n{imports_to_del}")
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

    # Update self.current_imports
    self.get_imports(db)

    return import_id

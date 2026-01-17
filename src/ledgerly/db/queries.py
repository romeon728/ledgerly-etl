import pandas as pd

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

def delete_imports(db, imports_to_del):
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

##################################################
# RULES SESSION
##################################################



##################################################
# TRANSACTIONS SESSION
##################################################

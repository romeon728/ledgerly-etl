from typing import List, Tuple
from ledgerly.db.connection import DatabaseConnection
from ledgerly.db.models import TransactionCreate


def get_or_create_account(bank_name: str, account_type: str, last_four: str) -> int:
    """Retrieves an account ID or creates it if it doesn't exist."""
    select_query = """
        SELECT account_id FROM accounts 
        WHERE bank_name = %s AND account_type = %s AND last_four = %s;
    """
    insert_query = """
        INSERT INTO accounts (bank_name, account_type, last_four)
        VALUES (%s, %s, %s)
        RETURNING account_id;
    """
    with DatabaseConnection.session() as conn:
        with conn.cursor() as cursor:
            cursor.execute(select_query, (bank_name, account_type, last_four))
            result = cursor.fetchone()
            if result:
                return result[0]
            
            cursor.execute(insert_query, (bank_name, account_type, last_four))
            return cursor.fetchone()[0]


def insert_transaction(txn: TransactionCreate) -> int:
    """Inserts an enriched transaction into the database[cite: 2]."""
    query = """
        INSERT INTO transactions (account_id, posted_date, description, amount, merchant, category, subcategory, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING transaction_id;
    """
    with DatabaseConnection.session() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    txn.account_id,
                    txn.posted_date,
                    txn.description,
                    txn.amount,
                    txn.merchant,
                    txn.category,
                    txn.subcategory,
                    txn.source,
                ),
            )
            return cursor.fetchone()[0]


def get_all_transactions() -> List[Tuple]:
    """Retrieves all stored transactions ordered by date descending."""
    query = """
        SELECT t.transaction_id, a.bank_name, a.account_type, t.posted_date, 
               t.description, t.amount, t.merchant, t.category, t.subcategory, t.source
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        ORDER BY t.posted_date DESC;
    """
    with DatabaseConnection.session() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
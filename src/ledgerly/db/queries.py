from typing import Optional, Any, List, Tuple
from ledgerly.db.connection import get_db_cursor
from ledgerly.db.models import TransactionCreate


def get_or_create_account(
    bank_name: str, account_type: str, last_four: str = "0000"
) -> int:
    """Retrieves an existing account_id or creates a new account record if it doesn't exist."""
    select_query = """
        SELECT account_id FROM accounts 
        WHERE bank_name = %s AND account_type = %s AND last_four = %s
        LIMIT 1;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(select_query, (bank_name, account_type, last_four))
        row = cur.fetchone()
        if row:
            return row[0]

    insert_query = """
        INSERT INTO accounts (bank_name, account_type, last_four)
        VALUES (%s, %s, %s)
        RETURNING account_id;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(insert_query, (bank_name, account_type, last_four))
        new_row = cur.fetchone()
        return new_row[0]


def transaction_exists(
    account_id: int, posted_date: Any, amount: float, description: str
) -> bool:
    """Fast indexed check to determine if a transaction already exists in PostgreSQL."""
    query = """
        SELECT 1 FROM transactions 
        WHERE account_id = %s AND posted_date = %s AND amount = %s AND description = %s
        LIMIT 1;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(query, (account_id, posted_date, amount, description))
        return cur.fetchone() is not None


def insert_transaction(txn: TransactionCreate) -> Optional[int]:
    """Inserts a transaction into PostgreSQL, ignoring duplicates via unique constraint."""
    query = """
        INSERT INTO transactions (
            account_id, posted_date, description, amount, 
            merchant, category, subcategory, source
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (account_id, posted_date, amount, description) 
        DO NOTHING
        RETURNING transaction_id;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(
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
        result = cur.fetchone()
        return result[0] if result else None


def get_all_transactions() -> List[Tuple]:
    """Retrieves all stored transactions for verification."""
    query = """
        SELECT transaction_id, bank_name, account_type, posted_date, 
               t.description, amount, merchant, category, subcategory, source
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        ORDER BY posted_date DESC;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(query)
        return cur.fetchall()
import hashlib
from typing import Optional, Any, List, Tuple
import pandas as pd

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
        SELECT bank_name, account_type, posted_date, 
               t.description, amount, merchant, category, subcategory
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        ORDER BY posted_date DESC;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(query)
        return cur.fetchall()

def get_transactions_df() -> pd.DataFrame:
    query = """
        SELECT 
            transaction_id,
            account_id,
            posted_date,
            description,
            amount,
            merchant,
            category,
            subcategory,
            source
        FROM transactions
        ORDER BY posted_date DESC;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(query)
        return pd.DataFrame(
            cur.fetchall(), 
            columns=[desc[0] for desc in cur.description]
        )


def get_all_tx_hashes() -> List[str]:
    """Retrieves SHA-256 hashes for all stored transactions to perform fast in-memory delta checks."""
    query = "SELECT posted_date, amount, description FROM transactions;"
    with get_db_cursor(commit=False) as cur:
        cur.execute(query)
        rows = cur.fetchall()

    hashes = []
    for posted_date, amount, description in rows:
        raw_key = f"{posted_date}|{float(amount):.2f}|{str(description).strip().lower()}"
        hashes.append(hashlib.sha256(raw_key.encode("utf-8")).hexdigest())

    return hashes

def insert_transactions_batch(txn_schemas: list[TransactionCreate]) -> list[int]:
    """Inserts a batch of transactions inside a single atomic transaction.
    
    Duplicates violating unique constraints are gracefully skipped.
    """
    if not txn_schemas:
        return []

    inserted_ids = []
    with get_db_cursor(commit=True) as cur:
        for txn in txn_schemas:
            cur.execute(
                """
                INSERT INTO transactions (
                    account_id, posted_date, description, amount, merchant, category, subcategory, source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (account_id, posted_date, amount, description) DO NOTHING
                RETURNING transaction_id;
                """,
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
            res = cur.fetchone()
            if res:
                inserted_ids.append(res[0])

    return inserted_ids

def insert_transactions_dataframe(df: pd.DataFrame, bank_name: str, account_type: str) -> list[int]:
    """Converts user-reviewed DataFrame rows into TransactionCreate models and commits them via batch insert."""
    if df.empty:
        return []

    txn_schemas = []
    for _, row in df.iterrows():
        txn = TransactionCreate(
            account_id=int(row["account_id"]),
            posted_date=row["posted_date"],
            description=str(row["description"]),
            amount=float(row["amount"]),
            merchant=row.get("merchant"),
            category=row.get("category"),
            subcategory=row.get("subcategory"),
            source=row.get("source", "user_staged"),
        )
        txn_schemas.append(txn)

    return insert_transactions_batch(txn_schemas)

def delete_transactions_by_ids(txn_ids: list[int]) -> int:
    """Deletes a list of transaction IDs from the database (used for rollback/undo)."""
    if not txn_ids:
        return 0

    with get_db_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM transactions WHERE transaction_id = ANY(%s);",
            (txn_ids,),
        )
        deleted_count = cur.rowcount

    return deleted_count
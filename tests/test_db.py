from datetime import date
import pytest
from ledgerly.db.models import AccountCreate, TransactionCreate


def test_account_create_schema():
    account = AccountCreate(
        bank_name="Chase", account_type="Checking", last_four="1234"
    )
    assert account.bank_name == "Chase"
    assert account.account_type == "Checking"
    assert account.last_four == "1234"


def test_transaction_create_schema():
    txn = TransactionCreate(
        account_id=1,
        posted_date=date(2026, 9, 1),
        description="Target Store",
        amount=45.99,
        merchant="Target",
        category="Shopping",
        subcategory="General",
        source="rule_engine",
    )
    assert txn.account_id == 1
    assert txn.amount == 45.99
    assert txn.category == "Shopping"
    assert txn.source == "rule_engine"
from unittest.mock import MagicMock, patch
import pytest
from ledgerly.db.models import TransactionCreate
from ledgerly.db.queries import delete_transactions_by_ids, insert_transactions_batch


@pytest.fixture
def sample_txns():
    return [
        TransactionCreate(
            account_id=1,
            posted_date="2026-09-01",
            description="COFFEE SHOP",
            amount=-4.50,
            merchant="Local Coffee",
            category="Food & Drink",
            subcategory="Coffee",
            source="csv",
        ),
        TransactionCreate(
            account_id=1,
            posted_date="2026-09-02",
            description="GROCERY STORE",
            amount=-52.10,
            merchant="Supermarket",
            category="Groceries",
            subcategory="Food",
            source="csv",
        ),
    ]


def test_insert_transactions_batch_empty():
    assert insert_transactions_batch([]) == []


@patch("ledgerly.db.queries.get_db_cursor")
def test_insert_transactions_batch_success(mock_get_cursor, sample_txns):
    mock_cur = MagicMock()
    # Simulate returning RETURNING transaction_id for each row
    mock_cur.fetchone.side_effect = [[101], [102]]
    mock_get_cursor.return_value.__enter__.return_value = mock_cur

    inserted_ids = insert_transactions_batch(sample_txns)

    assert inserted_ids == [101, 102]
    assert mock_cur.execute.call_count == 2


def test_delete_transactions_by_ids_empty():
    assert delete_transactions_by_ids([]) == 0


@patch("ledgerly.db.queries.get_db_cursor")
def test_delete_transactions_by_ids_success(mock_get_cursor):
    mock_cur = MagicMock()
    mock_cur.rowcount = 3
    mock_get_cursor.return_value.__enter__.return_value = mock_cur

    deleted_count = delete_transactions_by_ids([101, 102, 103])

    assert deleted_count == 3
    mock_cur.execute.assert_called_once_with(
        "DELETE FROM transactions WHERE transaction_id = ANY(%s);",
        ([101, 102, 103],),
    )
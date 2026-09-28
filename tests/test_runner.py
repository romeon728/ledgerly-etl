from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
import pandas as pd
import pytest
from ledgerly.pipeline.runner import ETLRunner


@pytest.fixture
def mock_parser():
    parser = MagicMock()
    parser.parse.return_value = pd.DataFrame(
        [
            {
                "posted_date": "2026-09-10",
                "description": "COFFEE SHOP",
                "amount": -4.50,
                "account_last_four": "1234",
            },
            {
                "posted_date": "2026-09-10",
                "description": "COFFEE SHOP",
                "amount": -4.50,
                "account_last_four": "1234",
            },  # Duplicate intra-batch row
            {
                "posted_date": "2026-09-11",
                "description": "GAS STATION",
                "amount": -35.00,
                "account_last_four": "1234",
            },
        ]
    )
    return parser


@pytest.fixture
def mock_enricher():
    enricher = MagicMock()
    enricher.enrich = AsyncMock(
        return_value={
            "merchant": "Test Merchant",
            "category": "Test Category",
            "subcategory": "Test Sub",
            "source": "vllm",
        }
    )
    return enricher


@pytest.mark.asyncio
@patch("ledgerly.pipeline.runner.insert_transactions_batch", return_value=[1, 2])
@patch("ledgerly.pipeline.runner.transaction_exists", return_value=False)
@patch("ledgerly.pipeline.runner.get_or_create_account", return_value=1)
async def test_run_pipeline_success_and_intra_batch_dedup(
    mock_get_account,
    mock_txn_exists,
    mock_insert_batch,
    mock_parser,
    mock_enricher,
):
    runner = ETLRunner(parser=mock_parser, enricher=mock_enricher)
    file_stream = BytesIO(b"fake,csv,content")

    progress_calls = []

    def progress_cb(current, total):
        progress_calls.append((current, total))

    result = await runner.run_pipeline(
        file_stream=file_stream,
        bank_name="TD Bank",
        account_type="Checking",
        progress_callback=progress_cb,
    )

    assert result["status"] == "success"
    assert result["processed_count"] == 2
    assert result["skipped_count"] == 1
    assert result["inserted_ids"] == [1, 2]

    mock_insert_batch.assert_called_once()
    assert len(mock_insert_batch.call_args[0][0]) == 2
    assert len(progress_calls) == 3


@pytest.mark.asyncio
@patch("ledgerly.pipeline.runner.insert_transactions_batch")
@patch("ledgerly.pipeline.runner.transaction_exists", return_value=False)
@patch("ledgerly.pipeline.runner.get_or_create_account", return_value=1)
async def test_run_pipeline_cancelled_midway(
    mock_get_account, 
    mock_txn_exists, 
    mock_insert_batch, 
    mock_parser, 
    mock_enricher
):
    runner = ETLRunner(parser=mock_parser, enricher=mock_enricher)
    file_stream = BytesIO(b"fake,csv,content")

    calls = 0

    def mock_cancel_check():
        nonlocal calls
        calls += 1
        return calls > 1

    result = await runner.run_pipeline(
        file_stream=file_stream,
        bank_name="TD Bank",
        account_type="Checking",
        cancel_check=mock_cancel_check,
    )

    assert result["status"] == "cancelled"
    assert result["processed_count"] == 0
    assert result["inserted_ids"] == []
    mock_insert_batch.assert_not_called()
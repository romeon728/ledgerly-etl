from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from ledgerly.pipeline.runner import ETLRunner


@pytest.mark.asyncio
async def test_etl_runner_pipeline_execution():
    # Simulated Checking CSV
    csv_data = (
        b"Date,Bank RTN,Account Number,Transaction Type,Description,Debit,Credit,Check Number,Account Running Balance\n"
        b"2024-12-24,1,1234,DEBIT,TOYOTA ACH RTL,740,,,\n"
        b"2024-12-18,1,1234,CREDIT,DIRECT DEP,,1585.11,,\n"
    )
    file_stream = BytesIO(csv_data)

    # Mock DB functions to prevent actual DB inserts during test
    with (
        patch(
            "ledgerly.pipeline.runner.get_or_create_account", return_value=1
        ) as mock_get_account,
        patch(
            "ledgerly.pipeline.runner.insert_transaction", return_value=101
        ) as mock_insert_txn,
    ):

        # Mock Enricher response
        mock_enricher = MagicMock()
        mock_enricher.enrich = AsyncMock(
            return_value={
                "merchant": "Test Merchant",
                "category": "Shopping",
                "subcategory": "General Retail",
                "source": "rule_engine",
            }
        )

        runner = ETLRunner(enricher=mock_enricher)
        result = await runner.run_pipeline(
            file_stream=file_stream,
            bank_name="Chase",
            account_type="Checking",
        )

        # Assertions
        assert result["status"] == "success"
        assert result["account_id"] == 1
        assert result["processed_count"] == 2

        # Ensure DB functions were called expected number of times
        mock_get_account.assert_called_once_with(
            bank_name="Chase", account_type="Checking", last_four="1234"
        )
        assert mock_insert_txn.call_count == 2
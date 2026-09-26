from typing import BinaryIO, Dict, Any, Optional
import pandas as pd
from ledgerly.extractors.csv_parser import CSVParser
from ledgerly.pipeline.enricher import TransactionEnricher
from ledgerly.db.queries import (
    get_or_create_account,
    insert_transaction,
    transaction_exists,
)
from ledgerly.db.models import TransactionCreate


class ETLRunner:
    """Orchestrates CSV parsing, deduplication, LLM enrichment, and PostgreSQL persistence."""

    def __init__(
        self,
        parser: Optional[CSVParser] = None,
        enricher: Optional[TransactionEnricher] = None,
    ):
        self.parser = parser or CSVParser()
        self.enricher = enricher or TransactionEnricher()

    async def run_pipeline(
        self, file_stream: BinaryIO, bank_name: str, account_type: str
    ) -> Dict[str, Any]:
        df = self.parser.parse(file_stream)

        if df.empty:
            return {
                "status": "success",
                "processed_count": 0,
                "skipped_count": 0,
            }

        sample_last_four = (
            df["account_last_four"].iloc[0]
            if "account_last_four" in df.columns
            else "0000"
        )
        account_id = get_or_create_account(
            bank_name=bank_name,
            account_type=account_type,
            last_four=str(sample_last_four),
        )

        inserted_count = 0
        skipped_count = 0

        for _, row in df.iterrows():
            posted_date = row["posted_date"]
            description = row["description"]
            amount = float(row["amount"])

            # 1. Deduplication Pre-check: Skip vLLM call entirely if record exists in DB
            if transaction_exists(account_id, posted_date, amount, description):
                skipped_count += 1
                continue

            # 2. Only run vLLM enrichment on NEW, unseen transactions
            enriched_data = await self.enricher.enrich(
                description=description,
                amount=amount,
                account_type=account_type,
            )

            txn_schema = TransactionCreate(
                account_id=account_id,
                posted_date=posted_date,
                description=description,
                amount=amount,
                merchant=enriched_data["merchant"],
                category=enriched_data["category"],
                subcategory=enriched_data["subcategory"],
                source=enriched_data["source"],
            )

            txn_id = insert_transaction(txn_schema)
            if txn_id:
                inserted_count += 1
            else:
                skipped_count += 1

        return {
            "status": "success",
            "account_id": account_id,
            "processed_count": inserted_count,
            "skipped_count": skipped_count,
        }
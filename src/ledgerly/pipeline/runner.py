from typing import BinaryIO, Dict, Any, Optional, Callable
import pandas as pd
from ledgerly.extractors.csv_parser import CSVParser
from ledgerly.pipeline.enricher import TransactionEnricher
from ledgerly.db.queries import (
    get_or_create_account,
    insert_transactions_batch,
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
        self,
        file_stream: BinaryIO,
        bank_name: str,
        account_type: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> Dict[str, Any]:
        df = self.parser.parse(file_stream)

        if df.empty:
            return {
                "status": "success",
                "processed_count": 0,
                "skipped_count": 0,
                "inserted_ids": [],
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

        skipped_count = 0
        txns_to_insert = []
        seen_in_batch = set()  # <-- Track transactions processed within this batch
        total_rows = len(df)

        for idx, (_, row) in enumerate(df.iterrows()):
            # Abort loop immediately if Cancel was clicked mid-way
            if cancel_check and cancel_check():
                return {
                    "status": "cancelled",
                    "processed_count": 0,
                    "skipped_count": 0,
                    "inserted_ids": [],
                }

            posted_date = row["posted_date"]
            description = row["description"]
            amount = float(row["amount"])
            
            # Key to identify duplicate transactions within the same file
            batch_key = (posted_date, amount, description)

            # 1. Deduplication Pre-check (DB check + Intra-batch check)
            if batch_key in seen_in_batch or transaction_exists(account_id, posted_date, amount, description):
                skipped_count += 1
                if progress_callback:
                    progress_callback(idx + 1, total_rows)
                continue

            seen_in_batch.add(batch_key)

            # 2. vLLM enrichment
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

            txns_to_insert.append(txn_schema)

            if progress_callback:
                progress_callback(idx + 1, total_rows)

        # Check cancellation one last time before database commit
        if cancel_check and cancel_check():
            return {
                "status": "cancelled",
                "processed_count": 0,
                "skipped_count": 0,
                "inserted_ids": [],
            }

        # Single atomic bulk insert (executes only if uninterrupted)
        inserted_ids = insert_transactions_batch(txns_to_insert)

        return {
            "status": "success",
            "account_id": account_id,
            "processed_count": len(inserted_ids),
            "skipped_count": skipped_count,
            "inserted_ids": inserted_ids,
        }
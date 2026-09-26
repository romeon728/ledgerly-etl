from typing import BinaryIO, Dict, Any, Optional
import pandas as pd
from ledgerly.extractors.csv_parser import CSVParser
from ledgerly.pipeline.enricher import TransactionEnricher
from ledgerly.db.queries import get_or_create_account, insert_transaction
from ledgerly.db.models import TransactionCreate


class ETLRunner:
    """Orchestrates CSV parsing, LLM/Rule enrichment, and PostgreSQL persistence."""

    def __init__(self, parser: Optional[CSVParser] = None, enricher: Optional[TransactionEnricher] = None):
        self.parser = parser or CSVParser()
        self.enricher = enricher or TransactionEnricher()

    async def run_pipeline(
        self, file_stream: BinaryIO, bank_name: str, account_type: str
    ) -> Dict[str, Any]:
        # Step 1: Extract standardized DataFrame from bank CSV export
        df = self.parser.parse(file_stream)
        
        if df.empty:
            return {"status": "success", "processed_count": 0}

        # Step 2: Resolve or Create Account metadata in Database
        sample_last_four = df["account_last_four"].iloc[0] if "account_last_four" in df.columns else "0000"
        account_id = get_or_create_account(
            bank_name=bank_name,
            account_type=account_type,
            last_four=str(sample_last_four),
        )

        processed_records = []

        # Step 3: Enrich each row and persist to PostgreSQL
        for _, row in df.iterrows():
            enriched_data = await self.enricher.enrich(
                description=row["description"],
                amount=row["amount"],
                account_type=account_type,
            )

            txn_schema = TransactionCreate(
                account_id=account_id,
                posted_date=row["posted_date"],
                description=row["description"],
                amount=float(row["amount"]),
                merchant=enriched_data["merchant"],
                category=enriched_data["category"],
                subcategory=enriched_data["subcategory"],
                source=enriched_data["source"],
            )

            txn_id = insert_transaction(txn_schema)
            processed_records.append(txn_id)

        return {
            "status": "success",
            "account_id": account_id,
            "processed_count": len(processed_records),
        }
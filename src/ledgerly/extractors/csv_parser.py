from typing import BinaryIO, Dict, Optional
import numpy as np
import pandas as pd
from ledgerly.extractors.base import BaseExtractor


class CSVParser(BaseExtractor):
    """Flexible CSV parser supporting unified amount or split Debit/Credit bank exports."""

    def parse(self, file_stream: BinaryIO) -> pd.DataFrame:
        df = pd.read_csv(file_stream)

        # Normalize column names (strip whitespace and lowercase)
        df.columns = [str(col).strip().lower() for col in df.columns]

        # 1. Standardize Date
        date_col = next((c for c in df.columns if "date" in c), None)
        if not date_col:
            raise ValueError("CSV missing a valid date column.")
        df["posted_date"] = pd.to_datetime(df[date_col]).dt.date

        # 2. Standardize Description
        desc_col = next(
            (
                c
                for c in df.columns
                if c in ["description", "payee", "name", "memo"]
            ),
            None,
        )
        if not desc_col:
            raise ValueError("CSV missing a valid description column.")
        df["description"] = df[desc_col].astype(str).str.strip()

        # 3. Handle Amount (Split Debit/Credit vs Single Amount Column)
        if "debit" in df.columns and "credit" in df.columns:
            # Convert empty values or strings to numeric floats
            debits = pd.to_numeric(df["debit"], errors="coerce").fillna(0.0)
            credits = pd.to_numeric(df["credit"], errors="coerce").fillna(0.0)

            # Debits are negative cash outflows, Credits are positive inflows
            df["amount"] = np.where(debits > 0, -debits, credits)
        elif "amount" in df.columns:
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(
                0.0
            )
        else:
            raise ValueError(
                "CSV must contain either an 'amount' column or 'debit' and 'credit' columns."
            )

        # 4. Extract Account Info if present (e.g., 'account number')
        account_col = next((c for c in df.columns if "account" in c), None)
        if account_col:
            df["account_last_four"] = (
                df[account_col].astype(str).str.strip().str[-4:]
            )
        else:
            df["account_last_four"] = "0000"

        # Return standardized DataFrame ready for ETL pipeline
        return df[
            ["posted_date", "description", "amount", "account_last_four"]
        ]
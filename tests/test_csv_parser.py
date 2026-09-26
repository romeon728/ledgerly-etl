from io import BytesIO
import pandas as pd
import pytest
from ledgerly.extractors.csv_parser import CSVParser


def test_csv_parser_checking_export():
    """Test parsing a checking account export with debit/credit columns."""
    csv_data = (
        b"Date,Bank RTN,Account Number,Transaction Type,Description,Debit,Credit,Check Number,Account Running Balance\n"
        b"2024-12-24,1,1234,DEBIT,TOYOTA ACH RTL,740,,,\n"
        b"2024-12-18,1,1234,CREDIT,DIRECT DEP,,1585.11,,\n"
    )
    file_stream = BytesIO(csv_data)

    parser = CSVParser()
    df = parser.parse(file_stream)

    assert len(df) == 2
    assert list(df.columns) == [
        "posted_date",
        "description",
        "amount",
        "account_last_four",
    ]

    # Checking Debit -> Negative Amount
    assert df.iloc[0]["description"] == "TOYOTA ACH RTL"
    assert df.iloc[0]["amount"] == -740.0
    assert df.iloc[0]["account_last_four"] == "1234"

    # Checking Credit -> Positive Amount
    assert df.iloc[1]["description"] == "DIRECT DEP"
    assert df.iloc[1]["amount"] == 1585.11
    assert df.iloc[1]["account_last_four"] == "1234"


def test_csv_parser_savings_export():
    """Test parsing a savings account export including running balance columns."""
    csv_data = (
        b"Date,Bank RTN,Account Number,Transaction Type,Description,Debit,Credit,Check Number,Account Running Balance\n"
        b"2024-12-31,1,3456,INT,INTEREST CREDIT,,20.69,,14262.81\n"
        b"2024-12-18,1,3456,XFER,Online Xfer Transfer to CK x4642,700,,,14242.12\n"
    )
    file_stream = BytesIO(csv_data)

    parser = CSVParser()
    df = parser.parse(file_stream)

    assert len(df) == 2
    assert list(df.columns) == [
        "posted_date",
        "description",
        "amount",
        "account_last_four",
    ]

    # Savings Credit -> Positive Amount
    assert df.iloc[0]["description"] == "INTEREST CREDIT"
    assert df.iloc[0]["amount"] == 20.69
    assert df.iloc[0]["account_last_four"] == "3456"

    # Savings Transfer Out (Debit) -> Negative Amount
    assert df.iloc[1]["description"] == "Online Xfer Transfer to CK x4642"
    assert df.iloc[1]["amount"] == -700.0
    assert df.iloc[1]["account_last_four"] == "3456"


def test_csv_parser_missing_required_columns():
    """Test error raising when essential columns (like date or amount/debit/credit) are missing."""
    csv_data = b"Account Number,Description\n1234,Unknown Store\n"
    file_stream = BytesIO(csv_data)

    parser = CSVParser()
    with pytest.raises(ValueError, match="CSV missing a valid date column."):
        parser.parse(file_stream)
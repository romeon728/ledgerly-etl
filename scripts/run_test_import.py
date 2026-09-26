import asyncio
from pathlib import Path
from ledgerly.pipeline.runner import ETLRunner


def run_import(csv_path: str, bank_name: str, account_type: str):
    path = Path(csv_path)
    if not path.exists():
        print(f"❌ File not found: {path.resolve()}")
        return

    print(f"🚀 Starting ETL processing for: {path.name}...")

    runner = ETLRunner()

    with open(path, "rb") as f:
        # Bridges synchronous def with the async run_pipeline method
        result = asyncio.run(
            runner.run_pipeline(
                file_stream=f, bank_name=bank_name, account_type=account_type
            )
        )

    print(
        f"✅ Import Complete for {path.name}! Processed {result['processed_count']} rows.\n"
    )


if __name__ == "__main__":
    # Call multiple CSV files sequentially with standard def function calls
    run_import(
        "scripts/tests/checking_transactions.csv",
        bank_name="TD Bank",
        account_type="Checking",
    )
    run_import(
        "scripts/tests/savings_transactions.csv",
        bank_name="TD Bank",
        account_type="Savings",
    )
#!/usr/bin/env python3

import argparse
import logging
from pathlib import Path
import csv
from datetime import datetime, date
import calendar
import os
from dotenv import load_dotenv
import json
import re

"""
parseCSV.py:

This script parses the given TD Bank CSV file based on the specified account type.

INFO: If this repo is just cloned, you'll need to create a .env file with the following information for this script to work
  BANK="" # Bank Name
  BANK_RTN="" # Banks Rounting Number
  CHECKING_ACCOUNT_NUMBER="" # Checking Account Number
  SAVINGS_ACCOUNT_NUMBER="" # Savings Account Number

Args:
  file (Path): Path to the input CSV file.
  account_type (str): Type of account for parsing [Checking, Savings].

Returns:
  Status code indicating success or failure.
"""

# Initialize ENV Variables
BANK = ""
BANK_RTN = ""
CHECKING_ACCOUNT_NUMBER = ""
SAVINGS_ACCOUNT_NUMBER = ""

def set_env():
  """
  Loads the information needed from your .env file
  """

  load_dotenv()  # load variables from .env

  global BANK, BANK_RTN, CHECKING_ACCOUNT_NUMBER, SAVINGS_ACCOUNT_NUMBER
  BANK = os.getenv("BANK")
  BANK_RTN = os.getenv("BANK_RTN")
  CHECKING_ACCOUNT_NUMBER = os.getenv("CHECKING_ACCOUNT_NUMBER")
  SAVINGS_ACCOUNT_NUMBER = os.getenv("SAVINGS_ACCOUNT_NUMBER")

  logging.info(f".env Config Information:\n\t- Bank: {BANK}\n\t- RTN: {BANK_RTN}\n\t- Checking Account: {CHECKING_ACCOUNT_NUMBER}\n\t- Savings Account: {SAVINGS_ACCOUNT_NUMBER}")

def parse_csv(file: Path) -> None:
  """
  parse the given statement CSV and load it into a JSON for further processing

  date, bank_rtn, account_number, _, description, debit, credit, _, _ = row 
    - Exclude [Transaction Type, Check Number, Account Running Balance]

  """
  
  logging.info("Parsing CSV: %s", file)
  
  # Parse the CSV file and write to dictionary
  parsed_data = {}
  with file.open("r", newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader) # Skip header

    raw_data = [tuple(row) for row in reader]
    
    # Determine statement period
    statement_start, statement_end = determine_statement_period(raw_data)
    parsed_data["statement_period"] = {
      "start": statement_start,
      "end": statement_end
    }

    # Determine account information
    account_type = determine_account_info(raw_data)
    parsed_data["account"] = {
      "bank": BANK,
      "type": account_type,
      "last_four": str(CHECKING_ACCOUNT_NUMBER)[-4:]
    }    

    # Parse transactions
    parsed_data["transactions"] = parse_transactions(raw_data)
  

  # Save parsed data to JSON
  file_path = "./data/transaction_data.json"
  logging.info(f"Dumping parsed data into JSON: {file_path}")

  directory = os.path.dirname(file_path)
  if not os.path.exists(directory):
    os.makedirs(directory)

  with open(file_path, 'w') as json_file:
    json.dump(parsed_data, json_file, indent=4)

  return 0

def determine_statement_period(raw_data:list) -> tuple[str,str]:
  """
  Determine the statement start and end dates for the given report
  """

  transaction_dates = [row[0] for row in raw_data]
  sorted_dates = sorted(transaction_dates, key=lambda d: datetime.strptime(d, "%Y-%m-%d"))
  
  ds = date.fromisoformat(sorted_dates[0])
  de = date.fromisoformat(sorted_dates[-1])

  first_date = date(ds.year, ds.month, 1).isoformat()
  last_date = date(de.year, de.month, 
    calendar.monthrange(de.year, de.month)[1]
  ).isoformat()

  return (first_date, last_date)

def determine_account_info(raw_data:list) -> str:
  """
  Determine the account type and confirm bank account number matches
  """
  
  def get_unique_list(raw_data, n):
    _list = []
    for row in raw_data:
      _value = row[n]
      if _value not in _list:
        _list.append(_value)
    return _list
  
  bank_rtn_list = get_unique_list(raw_data, 1)
  if len(bank_rtn_list) != 1:
    logging.error(f"More or less than one RTN found in CSV: {bank_rtn_list}")
    exit(1)
  bank_rtn = bank_rtn_list[0]
  if bank_rtn != BANK_RTN:
    logging.error(f"Bank RTN found in data does not match RTN on file: {bank_rtn}")
    exit(1)

  account_number_list = get_unique_list(raw_data, 2)
  if len(account_number_list) != 1:
    logging.error(f"More or less than one account number found in CSV. Script only supports 1 account type at a time: {account_number_list}")
    exit(1)
  account_number = account_number_list[0]
  account_type = ""
  if account_number == CHECKING_ACCOUNT_NUMBER:
    account_type = "Checking"
  elif account_number == SAVINGS_ACCOUNT_NUMBER:
    account_type = "Savings"
  else:
    logging.error(f"Unable to determine account type from account number found in CSV: {account_number}")
  
  return account_type

def parse_transactions(raw_data:list) -> list:
  """
  Parse all transactions from the raw csv into a list
  """
  transactions = []
  for row in raw_data:
    date, _, _, _, description, debit, credit, _, _ = row
    amount = 0
    if debit == "" or debit is None:
      amount = float(credit)
    elif credit == "" or credit is None:
      amount = float(debit) * -1
    else:
      logging.warning(f"Both debit and credit amounts empty for transaction (Date: {date}, Description: {description}); Skipping transaction")
      continue
    
    transaction = {
      "date": date,
      "description": re.sub(r'\s+', ' ', description).strip(),
      "amount": amount,
      "category": None,
      "merchant": None,
      "is_recurring": False
    }
    transactions.append(transaction)

  logging.info(f"Number of transactions collected: {len(transactions)}")
  return sorted(transactions, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"))


# ----------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------
if __name__ == "__main__":
  # Set up argument parser
  parser = argparse.ArgumentParser(description="Parse the given CSV file and Account Type")
  parser.add_argument("--file", type=Path, help="Path to the input CSV file")
  args = parser.parse_args()

  # Check if input file exists and is type CSV
  if not args.file.exists() or args.file.suffix.lower() != ".csv":
    logging.error("Input file does not exist or is not a CSV file: %s", args.file)
    exit(1)
  
  # Configure logging
  logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

  # Set environment variables
  set_env()

  # Call the parse function
  parse_csv(args.file)
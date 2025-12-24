#!/usr/bin/env python3

import logging
from logger_config import setup_logging

log_buffer = setup_logging()
logger = logging.getLogger("ledgerly")

import argparse
from pathlib import Path
import csv
from datetime import datetime
import os
from dotenv import load_dotenv
import re
import hashlib
import io

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


def parse_csv(uploaded_file) -> dict:
  """
  parse the given statement CSV and load it into a JSON for further processing

  date, bank_rtn, account_number, _, description, debit, credit, _, _ = row 
    - Exclude [Transaction Type, Check Number, Account Running Balance]

  """
  
  set_env()

  filename = uploaded_file.name
  logger.info("Parsing CSV: %s", filename)

  # Get the Hash (Binary Mode "rb")
  file_bytes = uploaded_file.getvalue()
  file_hash = hashlib.sha256(file_bytes).hexdigest()  

  # Parse the CSV file and write to dictionary
  string_data = file_bytes.decode("utf-8")
  reader = csv.reader(io.StringIO(string_data))
  next(reader) # Skip header

  raw_data = [tuple(row) for row in reader]

  # Build the data structure
  statement_start, statement_end = determine_statement_period(raw_data)
  account_type, last_four = determine_account_info(raw_data)
  parsed_data = {
    "import_info": {
      "filename": filename,
      "file_hash": file_hash,
      "row_count": len(raw_data)
    },
    "statement_period": {
      "start": statement_start,
      "end": statement_end
    },
    "account": {
      "bank": BANK,
      "type": account_type,
      "last_four": last_four
    },
    "transactions": parse_transactions(raw_data)
  }
  
  logger.info(f"Parsed {len(raw_data)} rows from {filename}")
  return parsed_data

# HELPER FUNCTIONS 

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

  logger.info(f".env Config Information:\n\t- Bank: {BANK}\n\t- RTN: x{BANK_RTN[-4:]}\n\t- Checking Account: x{CHECKING_ACCOUNT_NUMBER[-4:]}\n\t- Savings Account: x{SAVINGS_ACCOUNT_NUMBER[-4:]}")

def determine_statement_period(raw_data:list) -> tuple[str,str]:
  """
  Determine the statement start and end dates for the given report
  """

  transaction_dates = [row[0] for row in raw_data]
  sorted_dates = sorted(transaction_dates, key=lambda d: datetime.strptime(d, "%Y-%m-%d"))
  
  start_date = sorted_dates[0]
  end_date = sorted_dates[-1]

  logger.info(f"Start/End dates of transactions: {start_date} -> {end_date}")

  return (start_date, end_date)

def determine_account_info(raw_data:list) -> tuple[str,str]:
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
    logger.error(f"More or less than one RTN found in CSV: {bank_rtn_list}")
    exit(1)
  bank_rtn = bank_rtn_list[0]
  if bank_rtn != BANK_RTN:
    logger.error(f"Bank RTN found in data does not match RTN on file: {bank_rtn}")
    exit(1)

  account_number_list = get_unique_list(raw_data, 2)
  if len(account_number_list) != 1:
    logger.error(f"More or less than one account number found in CSV. Script only supports 1 account type at a time: {account_number_list}")
    exit(1)
  account_number = account_number_list[0]
  last_four = str(account_number)[-4:]
  account_type = ""
  if account_number == CHECKING_ACCOUNT_NUMBER:
    account_type = "Checking"
  elif account_number == SAVINGS_ACCOUNT_NUMBER:
    account_type = "Savings"
  else:
    logger.error(f"Unable to determine account type from account number found in CSV: {account_number}")
  
  return (account_type, last_four)

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
      logger.warning(f"Both debit and credit amounts empty for transaction (Date: {date}, Description: {description}); Skipping transaction")
      continue
    
    transaction = {
      "date": date,
      "description": re.sub(r'\s+', ' ', description).strip(),
      "amount": amount,
      "merchant": None,
      "category": None,
      "subcategory": None,
      "is_recurring": False
    }
    transactions.append(transaction)

  logger.info(f"Number of transactions collected: {len(transactions)}")
  return sorted(transactions, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"))


# ----------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------
def main():
  # Set up argument parser
  parser = argparse.ArgumentParser(description="Parse the given CSV file and Account Type")
  parser.add_argument("--file", type=Path, help="Path to the input CSV file")
  args = parser.parse_args()

  # Check if input file exists and is type CSV
  if isinstance(args.file, Path):
    if not args.file.exists() or args.file.suffix.lower() != ".csv":
      logger.error("Input file does not exist or is not a CSV file: %s", args.file)
      exit(1)
  
  # Set environment variables
  set_env()

  # Call the parse function
  parse_csv(args.file)

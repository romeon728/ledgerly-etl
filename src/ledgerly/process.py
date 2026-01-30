import pandas as pd
import math

import logging
from agents.logger_config import setup_logging
log_buffer = setup_logging()
logger = logging.getLogger("ledgerly")

import parser
import enrich

def process_transactions(uploaded_file, loaded_rules:list):
  # Parse and enrich transactions
  parsed_transactions = parser.parse_csv(uploaded_file)
  enriched_transactions = enrich.enrich_parsed_transactions(parsed_transactions, loaded_rules)
  enriched_transactions_df = convert_transactions_to_df(enriched_transactions)
  unknown_transactions_df = parse_unknown_transactions(enriched_transactions_df)
  return (
    enriched_transactions,
    enriched_transactions_df,
    unknown_transactions_df
  )

def convert_transactions_to_df(enriched_transactions:dict):
  enriched_transactions_df = pd.DataFrame(list(enriched_transactions["transactions"]))
  enriched_transactions_df['date'] = pd.to_datetime(enriched_transactions_df['date']).dt.date
  return enriched_transactions_df

def parse_unknown_transactions(enriched_transactions_df:pd.DataFrame):
  unknown_transactions_df = enriched_transactions_df[
    (enriched_transactions_df["merchant"] == "Unknown") & 
    (enriched_transactions_df["category"] == "Uncategorized")
  ]
  unknown_transactions_df = unknown_transactions_df.reset_index(drop=True)
  return unknown_transactions_df
import logging
from logger_config import setup_logging

log_buffer = setup_logging()
logger = logging.getLogger("ledgerly")

from db.rules import RulesEngine

"""
Cleans the transactions 
"""

def enrich_transaction(num_matches:int, tx:dict, re:RulesEngine):
  """
  Entrypoint for enriching transactions.
  """

  NUM_MATCHES = num_matches
  
  def unkown_description(rule:dict, description:str):
    if rule.get("merchant") == "Unknown" and rule.get("category") == "Uncategorized":
      logger.warning(f"Unknown Description: {description}")
      return True
    return False
  
  def matches(rule:dict, description:str):
    desc = description.upper()
    pattern = str(rule.get("match")).upper()

    if rule.get("match_type") == "contains" or rule.get("match_type") == "equals":
      if pattern in desc or pattern == desc: 
        nonlocal NUM_MATCHES
        NUM_MATCHES += 1
        return True
    return False

  description = tx.get("description")
  for rule in re.json_rules:
    # Skip inactive rules
    if not rule.get("active", True):
      continue
    
    # Enrich transaction
    # Check if description equals/contains the pattern
    # If Unknown (last rule in the list), set to uncategorized
    if matches(rule, description) or unkown_description(rule, description):
      tx["merchant"] = rule.get("merchant")
      tx["category"] = rule.get("category")
      tx["subcategory"] = rule.get("subcategory") or rule.get("category")
      tx["is_recurring"] = rule.get("is_recurring")
      tx["flow_type"] = "inflow" if tx["amount"] > 0 else "outflow"
      tx["rule_id"] = rule.get("id")

      return (NUM_MATCHES, tx)
    
    else:
      continue

  logger.error("INVESTIGATE WHY IT GOT THIS FAR")
  exit(1)


def enrich_parsed_transactions(parsed_transactions:dict, re:RulesEngine) -> dict:
  # Load merchant rules and account transactions
  re.load_json_rules()

  logger.info("Starting transaction enrichment...")
  logger.info(f"{len(parsed_transactions['transactions'])} Transactions Loaded")
  logger.info(f"\tStatement Period: {parsed_transactions['statement_period']['start']} -> {parsed_transactions['statement_period']['end']}")
  logger.info(f"\tAccount Information: {parsed_transactions['account']['bank']} | {parsed_transactions['account']['type']} x{parsed_transactions['account']['last_four']}")

  transactions = parsed_transactions["transactions"]
  enriched_transactions = []
  num_matches = 0
  for tx in transactions:
    num_matches, enriched_tx = enrich_transaction(num_matches, tx, re) 
    enriched_transactions.append(enriched_tx)

  logger.info(f"Matches found: {num_matches}/{len(transactions)}")
  enriched_data = {
    "import_info": parsed_transactions.get("import_info"),
    "statement_period": parsed_transactions.get("statement_period"),
    "account": parsed_transactions.get("account"),
    "transactions": enriched_transactions
  }

  logger.info("Finished transaction enrichment.")

  return enriched_data


# ----------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------
def main():  
  # Enrich transactions
  enrich_parsed_transactions()

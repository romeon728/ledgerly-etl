import logging
logger = logging.getLogger(__name__)

from db.rules import MerchantRules
merchant_rules = MerchantRules()
from db.transactions import AccountTransactions
account_transactions = AccountTransactions()

"""
Cleans the transactions 
"""

def enrich_transaction(tx:dict):
  """
  Entrypoint for enriching transactions.
  """
  
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
        logger.info(f"Matched: {desc} -> {pattern}")
        return True
    return False

  description = tx.get("description")
  for rule in merchant_rules.json_rules:
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

      return tx
    
    else:
      continue

  logger.error("INVESTIGATE WHY IT GOT THIS FAR")
  exit(1)


def enrich_parsed_transactions(parsed_transactions:dict) -> dict:
  # Load merchant rules and account transactions
  merchant_rules.load_json_rules()

  logger.info("Starting transaction enrichment...")
  logger.info(f"{len(parsed_transactions['transactions'])} Transactions Loaded")
  logger.info(f"\tStatement Period: {parsed_transactions['statement_period']['start']} -> {parsed_transactions['statement_period']['end']}")
  logger.info(f"\tAccount Information: {parsed_transactions['account']['bank']} | {parsed_transactions['account']['type']} x{parsed_transactions['account']['last_four']}")

  transactions = parsed_transactions["transactions"]
  enriched_transactions = [enrich_transaction(tx) for tx in transactions]

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

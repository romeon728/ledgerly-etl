import streamlit as st
import pandas as pd
from datetime import date
import json

import logging
from logger_config import setup_logging

log_buffer = setup_logging()
logger = logging.getLogger("ledgerly")

import parser
import enrich

from db.agents.database import LedgerlyDatabase
from db.rules import MerchantRules
from db.transactions import AccountTransactions

@st.cache_resource
def get_backend():
  db = LedgerlyDatabase()
  db.connect() # Establish connection once

  merchant_rules = MerchantRules()
  merchant_rules.load_rules(db)

  account_transactions = AccountTransactions()


  return db, merchant_rules, account_transactions

if "startup_done" not in st.session_state:
  # --- EVERYTHING IN THIS BLOCK RUNS ONLY ONCE ---  

  # --- PROCESS & UPLOAD TAB
  st.session_state.transactions_loaded = False

  # --- RULES TAB
  st.session_state.rules_data = [
    {"match_text": "", "match_type": "equals", "pattern": "", "category": "", "subcategory": "", "is_recurring": False, "priority": 10}
  ]
  st.session_state.rules_update_table_disabled = True
  st.session_state.rules_update_button_disabled = False
  st.session_state.rules_add_button_disabled = False

  st.session_state.rules_add_section_disabled= True
  
  # Set the flag to True so this block is skipped on the next rerun
  st.session_state.startup_done = True

  st.toast("Backend Connected", icon="✅")


# Page Config: Makes it wide-screen and gives it a title icon
st.set_page_config(page_title="Ledgerly", page_icon="💸", layout="wide")
st.title("💸 Ledgerly")
tab_process, tab_rules, tab_dashboard, tab_logs = st.tabs(["📤 Process & Upload", "⚙️ Rules Engine", "📊 Dashboard", "📜 Logs"])

# --- TAB 1: UPLOAD & ENRICH ---
with tab_process:
  col1, col2 = st.columns([1, 2])
  
  with col1:
    st.subheader("1. Input")
    uploaded_file = st.file_uploader("Upload Bank CSV", type=["csv"])
    
    if uploaded_file and not st.session_state.transactions_loaded:
      # This triggers your parsing pipeline automatically
      parsed_data = parser.parse_csv(uploaded_file)
      enriched_data = enrich.enrich_parsed_transactions(parsed_data)
      
      enriched_transactions_df = pd.DataFrame(list(enriched_data["transactions"]))
      enriched_transactions_df['date'] = pd.to_datetime(enriched_transactions_df['date']).dt.date
      
      st.success(f"Parsed {len(enriched_transactions_df)} transactions")
      st.session_state.transactions_loaded = True
      
      if st.button("🚀 Upload to Database", type="primary"):
        # logic.upload(df_enriched)
        st.toast("Transactions uploaded successfully!", icon="✅")
        st.session_state.transactions_loaded = False

  with col2:
    st.subheader("2. Review")
    st.caption("💡 Unrecognized transactions can be configured within the **⚙️ Rules Engine**.")
    if uploaded_file:
      st.data_editor(
        enriched_transactions_df,
        column_config={
          "date": st.column_config.DateColumn("Transaction Date",format="MMM DD, YYYY",help="The date the transaction cleared the bank"),
          "description": st.column_config.TextColumn("Description",help="Description of the transaction"),
          "amount": st.column_config.NumberColumn("Amount",help="Transaction value in USD"),
          "merchant": st.column_config.TextColumn("Merchant",help="The determined merchant of the transaction"),
          "category": st.column_config.TextColumn("Category",help="The determined category of the transaction"),
          "subcategory": st.column_config.TextColumn("Subcategory",help="The determined subcategory of the transaction"),
          "is_recurring": st.column_config.CheckboxColumn("Is Recurring",help="Checked if the transaction is recurring"),
          "flow_type": None,
          "rule_id": None
        },
        num_rows="dynamic",
        width='stretch',
        height=500,
        disabled=True
      )
    else:
      st.info("Waiting for CSV upload...")

# --- TAB 2: RULES ENGINE ---
with tab_rules:
  st.subheader("Rules Engine")

  # Buttons for Adding and Updating rules
  col1, col2 = st.columns([1, 6])
  with col1:
    if st.button("➕ Add", type="primary", disabled=st.session_state.rules_add_button_disabled):
      st.session_state.rules_add_section_disabled = False
      st.session_state.rules_add_button_disabled = True
      st.session_state.rules_update_button_disabled = True
      st.rerun()

  with col2:
    if st.button("🔧 Update", type="primary", disabled=st.session_state.rules_update_button_disabled):
      st.session_state.rules_update_table_disabled = False
      st.session_state.rules_add_button_disabled = True
      st.session_state.rules_update_button_disabled = True
      st.rerun()

    if not st.session_state.rules_update_table_disabled:
      if st.button("🏁 Confirm Updates", type="secondary"):
        st.info("Saving to database...")
        st.session_state.rules_update_table_disabled = True
        st.session_state.rules_add_button_disabled = False
        st.session_state.rules_update_button_disabled = False
        st.rerun()
  
  if not st.session_state.rules_add_section_disabled:
    st.divider()
    col1_1, col1_2 = st.columns([1, 6])
    with col1_1:
      if st.button("👍 Add New Rule(s)", type="secondary"):
        st.info("Saving to database...")
        st.session_state.rules_add_section_disabled = True
        st.session_state.rules_add_button_disabled = False
        st.session_state.rules_update_button_disabled = False
        st.rerun()

    with col1_2:
      edited_rules = st.data_editor(
        st.session_state["rules_data"],
        column_config={
          "match_text": st.column_config.TextColumn("Description Text", required=True, help="How the rule matches the transaction"),
          "match_type": st.column_config.SelectboxColumn("Match Type", options=["equals", "contains"], required=True, help="How the rule matches the transaction"),
          "merchant": st.column_config.TextColumn("Merchant", required=True, help="The merchant of the transaction"),
          "category": st.column_config.TextColumn("Category", required=True, help="The category of the transaction"),
          "subcategory": st.column_config.TextColumn("Subcategory", required=False, help="(Optional) The subcategory of the transaction"),
          "is_recurring": st.column_config.CheckboxColumn("Is Recurring", help="Checked if the transaction is recurring"),
          "priority": st.column_config.NumberColumn("Priority", help="The Priority of Match (0 being lowest pri, 10 being highest)", required=True, min_value=0, max_value=10, step=1, format="%d")
        },
        width='stretch',
        num_rows="dynamic"
      )

  # Rules Table
  st.divider()

  # List unkown transactions
  if uploaded_file:
    needs_rules_df = enriched_transactions_df[
      (enriched_transactions_df["merchant"] == "Unknown") & 
      (enriched_transactions_df["category"] == "Uncategorized")
    ]
    needs_rules_df = needs_rules_df.reset_index(drop=True)
    if needs_rules_df.empty:
      st.info("**All transactions are categorized!** There are no 'Unknown' merchants or 'Uncategorized' transactions to review.", icon="✨")
    else:
      st.data_editor(
        needs_rules_df,
        column_config={
          "date": st.column_config.DateColumn("Transaction Date",format="MMM DD, YYYY",help="The date the transaction cleared the bank"),
          "description": st.column_config.TextColumn("Description",help="Description of the transaction"),
          "amount": st.column_config.NumberColumn("Amount",help="Transaction value in USD"),
          "merchant": st.column_config.TextColumn("Merchant",help="The determined merchant of the transaction"),
          "category": st.column_config.TextColumn("Category",help="The determined category of the transaction"),
          "subcategory": st.column_config.TextColumn("Subcategory",help="The determined subcategory of the transaction"),
          "is_recurring": st.column_config.CheckboxColumn("Is Recurring",help="Checked if the transaction is recurring"),
          "flow_type": None,
          "rule_id": None
        },
        num_rows="dynamic",
        width='stretch',
        height=150,
        disabled=True
      )

  # List rules
  _, merchant_rules, _ = get_backend()
  merchant_rules_df = pd.DataFrame(merchant_rules.rules)
  merchant_rules_de = st.data_editor(
    merchant_rules_df,
    column_config={
      "rule_id": None,
      "created_at": None,
      "updated_at": None,
      "match_text": st.column_config.TextColumn("Description Text",help="How the rule matches the transaction"),
      "match_type": st.column_config.TextColumn("Match Type",help="How the rule matches the transaction"),
      "merchant": st.column_config.TextColumn("Merchant",help="The determined merchant of the transaction"),
      "category": st.column_config.TextColumn("Category",help="The determined category of the transaction"),
      "subcategory": st.column_config.TextColumn("Subcategory",help="The determined subcategory of the transaction"),
      "is_recurring": st.column_config.CheckboxColumn("Is Recurring",help="Checked if the transaction is recurring"),
      "priority": st.column_config.NumberColumn("Priority",help="Priority of description text",min_value=0,max_value=10,step=1,format="%d"),
      "active": st.column_config.CheckboxColumn("Active",help="Checked if the rule is currently active")
    },
    num_rows="dynamic",
    width='stretch',
    height=250,
    disabled=st.session_state.rules_update_table_disabled
  )

# --- TAB 4: LOGS ---
with tab_logs:
  st.subheader("System Logs")
  
  # Optional: Filter or Clear buttons
  col1, col2 = st.columns([1, 20])
  with col1:
    if st.button(label="", icon="🗑️", help="Clear Logs"):
      log_buffer.clear()
      logger.info("🧹 Logs cleared by user")
      st.rerun()
  with col2:
    if st.button(label="", icon="🔍", help="Filter"):
      logger.info(f"<TEST> LOG OUTPUT")
      st.rerun()

  # Join the deque of logs into one block of text
  # We convert to a list first because deques are specialized objects
  log_text = "\n".join(list(log_buffer))

  if log_text:
    # 'python' or 'bash' language provides nice coloring for timestamps/tags
    st.code(log_text, language="python")
  else:
    st.info("No logs captured yet. Try uploading a file!")
##### TODO
##### If unknown merchants found, show warning (yellow banner) below 2. Review with revised tip to look at Rules Engine

import streamlit as st
import pandas as pd

import logging
from logger_config import setup_logging

log_handler = setup_logging()
logger = logging.getLogger("ledgerly")

from db.agents.database import LedgerlyDatabase
from db.imports import ImportManager
from db.rules import RulesEngine
from db.transactions import AccountTransactions

@st.cache_resource
def get_backend():
  db = LedgerlyDatabase()
  im = ImportManager()
  re = RulesEngine()
  at = AccountTransactions()
  return db, im, re, at

# --- STARTUP ---
if "startup_done" not in st.session_state:
  # EVERYTHING IN THIS BLOCK RUNS ONLY ONCE
  
  # --- PROCESS & UPLOAD TAB
  st.session_state.file_uploader_n = 0
  st.session_state.transactions_loaded = False
  st.session_state.import_id = 0

  # --- RULES TAB
  st.session_state.rules_loaded = False
  st.session_state.rules_update_table_disabled = True
  st.session_state.rules_update_button_disabled = False
  st.session_state.rules_add_button_disabled = False
  st.session_state.rules_add_section_disabled= True

  # --- IMPORTS TAB
  st.session_state.imports_loaded = False

  # --- LOGS TAB
  st.session_state.filtered_module = None
  
  # Set the flag to True so this block is skipped on the next rerun
  st.session_state.startup_done = True
  st.toast("Backend Connected", icon="✅")

if "current_imports_df" not in st.session_state:
  db, im, _, _ = get_backend()
  im.get_imports(db)
  df = im.current_imports_df.copy()
  st.session_state.current_imports_df = df

# --- TOASTS ---
if st.session_state.get("upload_success"):
  _, _, _, at = get_backend()
  if at.num_tx_added == len(at.enriched_transactions_df):
    st.toast("All transactions uploaded successfully!", icon="✅")
  elif at.num_tx_added == 0:
    st.toast("No transactions were uploaded successfully.", icon="🚨")
  else:
    st.toast(f"{at.num_tx_added}/{len(at.enriched_transactions_df)} transactions uploaded successfully!", icon="✅")
    st.toast(f"{len(at.enriched_transactions_df) - at.num_tx_added} transactions skipped due to duplication.", icon="⚠️")
  del st.session_state.upload_success
if st.session_state.get("logs_cleared"):
  st.toast("Logs cleared by user", icon="🧹")
  del st.session_state.logs_cleared
if st.session_state.get("show_import_error"):
  st.toast("**Import Error:** The uploaded CSV already exists in Database.", icon="💀")
  del st.session_state.show_import_error
if st.session_state.get("import_delete_success"):
  st.toast("Selected imports successfully deleted.", icon="✅")
  del st.session_state.import_delete_success

# Page Config: Makes it wide-screen and gives it a title icon
st.set_page_config(page_title="Ledgerly", page_icon="💸", layout="wide")
st.title("💸 Ledgerly")
tab_process, tab_rules, tab_dashboard, tab_imports, tab_logs = st.tabs(["📤 Process & Upload", "⚙️ Rules Engine", "📊 Dashboard", "📂 Imports", "📜 Logs"])

# --- TAB 1: UPLOAD & ENRICH ---
with tab_process:
  col1, col2 = st.columns([1, 2])
  
  with col1:
    st.subheader("1. Input")
    uploaded_file = st.file_uploader("Upload Bank CSV", type=["csv"], key=f"uploader_{st.session_state.file_uploader_n}")
    
    if uploaded_file:
      # This triggers your parsing pipeline automatically
      if not st.session_state.transactions_loaded:
        _, _, re, at = get_backend()
        at.process_transactions(uploaded_file, re)
        st.toast("Transactions Loaded", icon="✅")
        st.success(f"Parsed {len(at.enriched_transactions_df)} transactions")
        st.session_state.transactions_loaded = True
      
      if st.session_state.get("confirm_phase"):
        st.write("🤔 Have you reviewed your transaction?")
        col1_1, col1_2 = st.columns(2)
        if col1_1.button("👍 Confirm", use_container_width=True, type="primary"):
          db, im, _, at = get_backend()
          st.session_state.import_id = im.add_import(db, at.enriched_transactions)
          if st.session_state.import_id == 0:
            st.session_state.show_import_error = True
            st.rerun()

          # If no import error, upload to DB
          result = at.add_transactions(db, st.session_state.import_id)

          st.session_state.confirm_phase = False
          st.session_state.transactions_loaded = False
          st.session_state.file_uploader_n += 1
          st.session_state.upload_success = True
          del st.session_state.current_imports_df
          st.rerun()
        if col1_2.button("👎 Cancel", use_container_width=True):
          st.session_state.confirm_phase = False
          st.rerun()
      
      else:
        if st.button("🚀 Upload to Database", type="primary"):
          st.session_state.confirm_phase = True
          st.rerun()
    
    else:
      st.session_state.transactions_loaded = False

  with col2:
    st.subheader("2. Review")
    _, _, _, at = get_backend()
    if st.session_state.transactions_loaded and not at.unknown_transactions_df.empty:
      st.warning(f"{len(at.unknown_transactions_df)} Unknown Transactions found.")
    st.caption("💡 Unrecognized transactions can be configured within the **⚙️ Rules Engine**.")
    if uploaded_file:
      st.data_editor(
        at.enriched_transactions_df,
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
  col1, col2 = st.columns([1, 12])
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
    st.divider()
    col2_1, col2_2 = st.columns([1, 6])
    with col2_1:
      if st.button("🏁 Confirm Updates", type="secondary"):
        st.info("Saving to database...")
        st.session_state.rules_update_table_disabled = True
        st.session_state.rules_loaded = False
        st.session_state.rules_add_button_disabled = False
        st.session_state.rules_update_button_disabled = False
        st.rerun()
    with col2_2:
      st.caption("💡 You can't delete rules, but you can de-activate them by unchecking **Active**.")
  
  if not st.session_state.rules_add_section_disabled:
    st.divider()
    col1_1, col1_2 = st.columns([1, 6])
    with col1_1:
      if st.button("👍 Add New Rule(s)", type="secondary"):
        st.info("Saving to database...")
        st.session_state.rules_add_section_disabled = True
        st.session_state.rules_loaded = False
        st.session_state.rules_add_button_disabled = False
        st.session_state.rules_update_button_disabled = False
        st.rerun()

    with col1_2:
      edited_rules = st.data_editor(
        [{"match_text": "", "match_type": "equals", "merchant": "", "category": "", "subcategory": "", "is_recurring": False, "priority": 10}],
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
    _, _, _, at = get_backend()
    if at.unknown_transactions_df.empty:
      st.info("**All transactions are categorized!** There are no 'Unknown' merchants or 'Uncategorized' transactions to review.", icon="✨")
    else:
      st.data_editor(
        at.unknown_transactions_df,
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
  # Only load rules on start or when rules are updated
  db, _, re, _ = get_backend()
  if not st.session_state.rules_loaded:
    re.load_rules(db)
    st.toast("Rules Loaded", icon="✅")
    st.session_state.rules_loaded = True

  merchant_rules_de = st.data_editor(
    pd.DataFrame(re.rules),
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
    height=350,
    disabled=st.session_state.rules_update_table_disabled
  )

# --- TAB 3: DASHBOARD ---
with tab_dashboard:
  st.subheader("Dashboard")
  grafana_url = "http://localhost:3000/d/adl5rnw/ledgerly?orgId=1&from=now-1y&to=now&timezone=browser&var-bank=TD%20Bank"
  grafana_msg = "View Ledgerly Grafana Report"
  st.markdown(
    """
    <style>
    .custom-link {
      text-decoration: none;
      color: #ff4b4b; /* Streamlit Red */
      font-weight: 500;
    }
    .custom-link:hover {
      text-decoration: underline;
    }
    </style>
    <a class="custom-link" href="http://localhost:3000/d/adl5rnw/ledgerly?orgId=1&from=now-1y&to=now&timezone=browser&var-bank=TD%20Bank" target="_blank">
      View Ledgerly Grafana Report
    </a>
    """, 
    unsafe_allow_html=True
  )

# --- TAB 4: IMPORTS ---
with tab_imports:
  st.subheader("Imports Manager")
  db, im, _, _ = get_backend()
  current_imports_de = st.data_editor(
    st.session_state.current_imports_df,
    column_config={
      "is_selected": st.column_config.CheckboxColumn("Selected",help="Toggle to be deleted upon selection"),
      "bank": st.column_config.TextColumn("Bank",help="The bank holding the transactions"),
      "filename": st.column_config.TextColumn("File Name",help="The filename of the imported CSV"),
      "start_date": st.column_config.DateColumn("Start Date",help="The start date of the transactions",format="YYYY-MM-DD"),
      "end_date": st.column_config.DateColumn("End Date",help="The end date of the transactions",format="YYYY-MM-DD"),
      "row_count": st.column_config.TextColumn("Num Transactions",help="The number of transactions within the CSV"),
      "account_type": st.column_config.TextColumn("Account Type",help="The account type (Checking, Savings, Credit, etc.)"),
      "account_number": st.column_config.TextColumn("Account Number (Last 4)",help="The account number (x####)"),
    },
    num_rows="dynamic",
    width='stretch',
    height=250,
    disabled=[
      c for c in st.session_state.current_imports_df.columns
      if c != "is_selected"
    ],
    key="imports_data_editor"
  )
  if st.button("🗑️ Delete Selected Imports", type="primary"):
    selected_data = current_imports_de[current_imports_de["is_selected"]]    
    if selected_data.empty:
      st.error("No rows selected!")
    else:
      im.delete_imports(db, selected_data)
      st.session_state.import_delete_success = True
      del st.session_state.current_imports_df
      st.rerun()

# --- TAB 5: LOGS ---
with tab_logs:
  st.subheader("System Logs")
  
  col1, col2 = st.columns([1, 20])
  with col1:
    if st.button(label="", icon="🗑️", help="Clear Logs"):
      log_handler.clear_history()
      st.session_state.logs_cleared = True
      st.session_state.filtered_module = None
      st.rerun()
  with col2:
    default_ix = log_handler.get_modules().index("All")
    log_module_selection = st.selectbox(
      label="Filter Logs",
      options=log_handler.get_modules(),
      index=default_ix,
      help="Select a module to filter logs",
      label_visibility="collapsed" # Removes the top label for a 'search bar' feel
  )
    
  # Join the deque of logs into one block of text
  # We convert to a list first because deques are specialized objects
  log_text = "\n".join(log_handler.get_logs(log_module_selection))

  if log_text:
    # 'python' or 'bash' language provides nice coloring for timestamps/tags
    st.code(log_text, language="python")
  else:
    st.info("No logs captured yet. Try uploading a file!")
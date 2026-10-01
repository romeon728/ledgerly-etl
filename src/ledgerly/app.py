import streamlit as st
import asyncio
from ledgerly.pipeline.runner import ETLRunner
from ledgerly.views import upload, report, transactions, rules, dashboard, about

st.set_page_config(page_title="Ledgerly", page_icon="💸", layout="wide")
st.title("💸 Ledgerly")

@st.cache_resource
def get_etl_runner():
    return ETLRunner()

runner = get_etl_runner()

tab_upload, tab_report, tab_transactions, tab_rules, tab_dashboard, tab_about = st.tabs([
    "📤 Process & Upload", 
    "💾 Save Report",
    "📂 Transactions", 
    "📜 Rules",
    "📊 Dashboard", 
    "💡 About"
])

with tab_upload:
    upload.render(runner)

with tab_report:
    report.render()

with tab_transactions:
    transactions.render()

with tab_rules:
    rules.render()

with tab_dashboard:
    dashboard.render()

with tab_about:
    about.render()
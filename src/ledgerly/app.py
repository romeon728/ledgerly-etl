import streamlit as st
from pathlib import Path
import base64

from ledgerly.pipeline.runner import ETLRunner
from ledgerly.views import upload, report, transactions, rules, dashboard, about

# Resolve paths
CURRENT_FILE = Path(__file__).resolve()

# Check for assets at /app/assets (container root) or ./assets (project root)
POSSIBLE_PATHS = [
    CURRENT_FILE.parent.parent.parent / "assets" / "icon.png",  # /app/assets
    CURRENT_FILE.parent.parent / "assets" / "icon.png",         # /app/src/assets
    Path("assets/icon.png").resolve(),
]

ICON_PATH = next((p for p in POSSIBLE_PATHS if p.exists()), None)
ICON_PNG = str(ICON_PATH) if ICON_PATH else "💸"  # Fallback to emoji if file missing

# Update browser tab icon
st.set_page_config(page_title="Ledgerly", page_icon=ICON_PNG, layout="wide")

# Encode image for inline rendering
if ICON_PATH:
    with open(ICON_PATH, "rb") as f:
        icon_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 10px;">
            <img src="data:image/png;base64,{icon_b64}" style="width: 64px; height: 64px; object-fit: contain;" />
            <h1 style="margin: 0; padding: 0; font-size: 2.25rem; font-weight: 700; line-height: 1;">Ledgerly</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
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
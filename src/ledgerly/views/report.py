import io
import re
import os
import openpyxl
import pandas as pd
import streamlit as st
from datetime import datetime

from ledgerly.db.queries import get_transactions_df
from ledgerly.services.expense_report_service import ExpenseReportGenerator


def parse_owner_from_filename(filename: str) -> str | None:
    """Extracts and restores the original owner name from a Ledgerly report filename.
    
    Example:
        'Ledgerly_Report-John_Doe.xlsx' -> 'John Doe'
        'Ledgerly_Report-Nick.xlsx'     -> 'Nick'
    """
    base_name = os.path.basename(filename)
    match = re.search(r"^Ledgerly_Report-(.*?)\.xlsx$", base_name, re.IGNORECASE)
    
    if match:
        extracted = match.group(1)
        # Reverse the transformation: replace underscores back to spaces
        return extracted.replace("_", " ").strip()
    
    return None


def get_existing_master_months(file_bytes: bytes) -> list[str]:
    """Inspects uploaded ledger report to extract already populated month tabs."""
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True)
        date_pattern = re.compile(r"^\d{4}-\d{2}$")
        return [s for s in wb.sheetnames if date_pattern.match(s)]
    except Exception as e:
        st.warning(f"Could not parse month sheets from Ledger Report: {e}")
        return []


def on_master_file_upload():
    """Callback triggered when a file is uploaded to parse and populate the owner name."""
    uploaded = st.session_state.get("master_file_uploader")
    if uploaded:
        parsed_name = parse_owner_from_filename(uploaded.name)
        if parsed_name:
            st.session_state["owner_name"] = parsed_name


def render():
    st.title("📑 Expense Report")
    st.write(
        "Generate styled multi-month Excel expense reports or update an existing Ledger Report."
    )

    # Initialize state for owner_name if not already present
    if "owner_name" not in st.session_state:
        st.session_state["owner_name"] = ""

    df = get_transactions_df()

    if df is None or df.empty:
        st.warning("No transactions found in the database. Please upload bank data first.")
        return

    col1, col2 = st.columns([1, 1])

    # 1. Ledger Report Section
    existing_months = []
    current_month = datetime.now().strftime('%Y-%m')
    master_bytes = None

    with col1:
        st.subheader("1. Ledger Report")
        uploaded_master = st.file_uploader(
            "Import existing Ledger Expense Report (.xlsx)",
            type=["xlsx"],
            key="master_file_uploader",
            on_change=on_master_file_upload,
        )
        if uploaded_master:
            master_bytes = uploaded_master.getvalue()
            existing_months = get_existing_master_months(master_bytes)
            st.success(f"Ledger Report loaded. Found {len(existing_months)} existing month tab(s).")
        else:
            st.info(
                "💡 **Ledger Report Behavior:**\n"
                "- **New Report:** If no file is uploaded, a new Ledger Report will be created.\n"
                "- **Existing Report:** If uploaded, new months are appended chronologically without overwriting existing tabs."
            )

    # 2. Settings Section
    with col2:
        st.subheader("2. Report Details & Months")

        owner_name = st.text_input(
            "Report Owner",
            placeholder="e.g. John Doe",
            key="owner_name",
        )

        # Extract available YYYY-MM options from DB data
        df["posted_date"] = pd.to_datetime(df["posted_date"])
        available_months = (
            df["posted_date"].dt.strftime("%Y-%m").unique().tolist()
        )
        available_months.sort(reverse=True)

        # Set current_month to the newest month present in your data
        current_month = available_months[0] if available_months else datetime.now().strftime('%Y-%m')

        # Exclude existing tabs AND current month from unpopulated list (used for "Select All New Months")
        unpopulated_months = [
            m for m in available_months 
            if m not in existing_months and m != str(current_month).strip()
        ]

        # Initialize session state for selected months to empty if not present
        if "selected_months_list" not in st.session_state:
            st.session_state["selected_months_list"] = []

        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("✨ Select All New Months", use_container_width=True):
                st.session_state["selected_months_list"] = unpopulated_months
                st.rerun()

        with col_btn2:
            if st.button("🧹 Clear Selection", use_container_width=True):
                st.session_state["selected_months_list"] = []
                st.rerun()

        selected_months = st.multiselect(
            "Select Month(s) to Export",
            options=available_months,
            key="selected_months_list",
            format_func=lambda m: (
                f"🔒 {str(m).strip()} (Already in Ledger)" if str(m).strip() in existing_months
                else f"⏳ {str(m).strip()} (Current Month)" if str(m).strip() == str(current_month).strip()
                else str(m).strip()
            )
        )

        # Filter selection to valid, non-locked, closed months
        exportable_months = [m for m in selected_months if m not in existing_months and m != str(current_month).strip()]
        
        if len(selected_months) != len(exportable_months):
            if str(current_month).strip() in selected_months:
                st.caption("⏳ *Current month will not be added to Ledger report*")
            if any(m in existing_months for m in selected_months):
                st.caption("ℹ️ *Locked months already exist in the Ledger report*")
    # 3. Execution
    if st.button("🚀 Generate Expense Report", type="primary", disabled=not bool(owner_name and owner_name.strip())):
        if not exportable_months:
            st.error("Please select at least one valid completed month.")
            return

        user_info = {"name": owner_name}

        generator = ExpenseReportGenerator(df)
        excel_buffer = generator.generate_report(
            months_selected=exportable_months,
            user_info=user_info,
            master_file_bytes=master_bytes,
        )

        clean_name = owner_name.strip().replace(" ", "_")
        
        filename = f"Ledgerly_Report-{clean_name}.xlsx"

        st.success("Report created successfully!")
        st.download_button(
            label="📥 Download Excel Report",
            data=excel_buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
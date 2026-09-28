from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

from ledgerly.db.queries import get_all_transactions

# Standard tuple schema fallback if database query returns unlabelled rows
DEFAULT_COLUMNS = [
    "bank",
    "account",
    "date",
    "description",
    "amount",
    "merchant",
    "category",
    "subcategory",
]

@st.cache_data(ttl=300)
def load_transaction_data() -> pd.DataFrame:
    """Fetch transactions from PostgreSQL and convert to a clean Pandas DataFrame."""
    raw_txns = get_all_transactions()
    if not raw_txns:
        return pd.DataFrame()

    df = pd.DataFrame(raw_txns)

    # Automatically fix unlabelled tuple columns (0, 1, 2, 3...)
    if not df.empty and isinstance(df.columns[0], (int, type(0))):
        df.columns = DEFAULT_COLUMNS[: len(df.columns)]
    else:
        # Standardize existing column headers to lowercase
        df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]

    # Convert data types safely
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)

    return df

def render():
    st.title("💳 Database Transactions")

    df = load_transaction_data()

    if df.empty:
        st.info(
            "No transactions found in the database. Head over to **Process & Upload** to import your first statement!"
        )
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        return

    # ------------------------------------------------------------------
    # Safeguard: Compute Strict Date Range Bounds
    # ------------------------------------------------------------------
    valid_dates = df["date"].dropna() if "date" in df.columns else []

    if len(valid_dates) > 0:
        min_date = min(valid_dates)
        max_date = max(valid_dates)
    else:
        min_date = datetime.today().date()
        max_date = datetime.today().date()

    if min_date > max_date:
        min_date, max_date = max_date, min_date

    # ------------------------------------------------------------------
    # 1. Interactive Filter Toolbar
    # ------------------------------------------------------------------
    row1_col1, row1_col2, row1_col3 = st.columns([2.5, 2.5, 1])

    with row1_col1:
        search_query = st.text_input(
            "🔍 Search Description",
            value="",
            placeholder="e.g. Chipotle, Amazon, Gas...",
        )

    with row1_col2:
        available_categories = (
            sorted([str(c) for c in df["category"].dropna().unique()])
            if "category" in df.columns
            else []
        )
        selected_categories = st.multiselect(
            "🏷️ Categories",
            options=available_categories,
            default=[],
            placeholder="All Categories",
        )

    with row1_col3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    row2_col1, row2_col2 = st.columns([2, 3])

    with row2_col1:
        preset_option = st.selectbox(
            "⏱️ Quick Time Range",
            options=[
                "All Time",
                "Last 30 Days",
                "Last 60 Days",
                "Last 90 Days",
                "Last 6 Months",
                "Last 1 Year",
                "Custom Range",
            ],
            index=0,
        )

    # Compute default date limits based on preset selections
    if preset_option == "Last 30 Days":
        default_start = max(min_date, max_date - timedelta(days=30))
        default_end = max_date
    elif preset_option == "Last 60 Days":
        default_start = max(min_date, max_date - timedelta(days=60))
        default_end = max_date
    elif preset_option == "Last 90 Days":
        default_start = max(min_date, max_date - timedelta(days=90))
        default_end = max_date
    elif preset_option == "Last 6 Months":
        default_start = max(min_date, max_date - timedelta(days=180))
        default_end = max_date
    elif preset_option == "Last 1 Year":
        default_start = max(min_date, max_date - timedelta(days=365))
        default_end = max_date
    else:  # "All Time" or "Custom Range"
        default_start = min_date
        default_end = max_date

    with row2_col2:
        if min_date == max_date:
            st.info(f"📅 All transactions occurred on: **{min_date}**")
            start_d, end_d = min_date, max_date
        else:
            date_range = st.date_input(
                "📅 Active Date Range",
                value=(default_start, default_end),
                min_value=min_date,
                max_value=max_date,
                disabled=(preset_option != "Custom Range"),
            )

            # Safeguard: Handle intermediate calendar clicks
            if isinstance(date_range, (list, tuple)):
                if len(date_range) == 2:
                    start_d, end_d = date_range
                elif len(date_range) == 1:
                    start_d = date_range[0]
                    end_d = date_range[0]
                else:
                    start_d, end_d = min_date, max_date
            else:
                start_d = date_range
                end_d = date_range

    # ------------------------------------------------------------------
    # 2. Filter Application Logic
    # ------------------------------------------------------------------
    filtered_df = df.copy()

    # Text Search Filter
    if search_query and "description" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["description"]
            .astype(str)
            .str.contains(search_query, case=False, na=False)
        ]

    # Category Multi-Select Filter
    if selected_categories and "category" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["category"].astype(str).isin(selected_categories)
        ]

    # Date Range Filter
    if "date" in filtered_df.columns and start_d and end_d:
        filtered_df = filtered_df[
            (filtered_df["date"] >= start_d) & (filtered_df["date"] <= end_d)
        ]

    # ------------------------------------------------------------------
    # 3. Dynamic Metrics / KPIs
    # ------------------------------------------------------------------
    st.markdown("---")

    col_kpi, col_toggle = st.columns([3, 1])
    with col_toggle:
        exclude_transfers = st.checkbox(
            "🚫 Exclude Transfers",
            value=True,
            help="Excludes internal account transfers and credit card payments from Income and Expense totals.",
        )

    # Filter dataset for KPI calculation if transfer exclusion is active
    kpi_df = filtered_df.copy()

    if exclude_transfers and "category" in kpi_df.columns:
        transfer_categories = [
            "Financial & Transfers",
            "Account Transfer",
            "Credit Card Payment",
            "Transfer",
        ]
        kpi_df = kpi_df[
            ~kpi_df["category"].astype(str).str.title().isin(transfer_categories)
        ]

    total_txns = len(filtered_df)
    net_total = (
        filtered_df["amount"].sum() if "amount" in filtered_df.columns else 0.0
    )

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Total Transactions", f"{total_txns:,}")
    m2.metric("Net Total Amount", f"${net_total:,.2f}")

    if "amount" in kpi_df.columns:
        income = kpi_df[kpi_df["amount"] > 0]["amount"].sum()
        expenses = kpi_df[kpi_df["amount"] < 0]["amount"].sum()
        m3.metric("Total Income", f"${income:,.2f}")
        m4.metric("Total Expenses", f"${abs(expenses):,.2f}")

# ------------------------------------------------------------------
    # 4. Formatted Data Table
    # ------------------------------------------------------------------
    st.markdown("### Transaction Details")

    column_config = {
        "bank": "Bank",
        "account": "Account",
        "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
        "description": "Description",
        "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
        "merchant": "Merchant",
        "category": "Category",
        "subcategory": "Subcategory",
    }

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )
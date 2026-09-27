from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

from ledgerly.db.queries import get_all_transactions


@st.cache_data(ttl=300)
def load_transaction_data() -> pd.DataFrame:
    """Fetch transactions from PostgreSQL and convert to a clean Pandas DataFrame."""
    raw_txns = get_all_transactions()
    if not raw_txns:
        return pd.DataFrame()

    df = pd.DataFrame(raw_txns)

    # Convert data types safely
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date
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
    # Safeguard: Calculate Strict Date Bounds from Database
    # ------------------------------------------------------------------
    valid_dates = (
        df["date"].dropna()
        if "date" in df.columns
        else pd.Series(dtype="object")
    )

    if not valid_dates.empty:
        min_date = min(valid_dates)
        max_date = max(valid_dates)
    else:
        min_date = datetime.today().date()
        max_date = datetime.today().date()

    # Ensure min_date never exceeds max_date
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
            sorted(df["category"].dropna().unique().tolist())
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

            # Safeguard: Handle date_input returns while user is actively picking dates
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
            filtered_df["category"].isin(selected_categories)
        ]

    # Date Range Filter
    if "date" in filtered_df.columns and start_d and end_d:
        filtered_df = filtered_df[
            (filtered_df["date"] >= start_d) & (filtered_df["date"] <= end_d)
        ]

    # ------------------------------------------------------------------
    # 3. Dynamic Metrics / KPIs
    # ------------------------------------------------------------------
    total_txns = len(filtered_df)
    net_total = (
        filtered_df["amount"].sum()
        if "amount" in filtered_df.columns
        else 0.0
    )

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Total Transactions", f"{total_txns:,}")
    m2.metric("Net Total Amount", f"${net_total:,.2f}")

    if "amount" in filtered_df.columns:
        income = filtered_df[filtered_df["amount"] > 0]["amount"].sum()
        expenses = filtered_df[filtered_df["amount"] < 0]["amount"].sum()
        m3.metric("Total Income", f"${income:,.2f}")
        m4.metric("Total Expenses", f"${abs(expenses):,.2f}")

    # ------------------------------------------------------------------
    # 4. Formatted Data Table
    # ------------------------------------------------------------------
    st.markdown("### Transaction Details")

    column_config = {}
    if "amount" in filtered_df.columns:
        column_config["amount"] = st.column_config.NumberColumn(
            "Amount", format="$%.2f"
        )
    if "date" in filtered_df.columns:
        column_config["date"] = st.column_config.DateColumn(
            "Date", format="YYYY-MM-DD"
        )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )
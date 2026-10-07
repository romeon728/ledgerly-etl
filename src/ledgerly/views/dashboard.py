import calendar
from datetime import date, datetime, timedelta
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ledgerly.db.queries import get_transactions_df
from ledgerly.db.rules import get_all_rules


def render():
    st.title("📊 Financial Overview")

    df = get_transactions_df()

    if df is None or df.empty:
        st.warning("No transactions found in the database. Please upload bank data first.")
        return

    # -------------------------------------------------------------------------
    # DATA PREPARATION & TYPE SANITIZATION
    # -------------------------------------------------------------------------
    df = df.copy()

    # Ensure posted_date is in datetime format
    date_col = "posted_date" if "posted_date" in df.columns else "date"
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    # Ensure amount is numeric float
    amount_col = "amount"
    if amount_col in df.columns:
        df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0.0)

    # Standardize string columns
    category_col = "category" if "category" in df.columns else "description"
    subcat_col = "subcategory" if "subcategory" in df.columns else category_col
    desc_col = "description" if "description" in df.columns else category_col
    merchant_col = "merchant" if "merchant" in df.columns else desc_col
    account_col = "account_name" if "account_name" in df.columns else "account"

    for col in [category_col, subcat_col, desc_col, merchant_col, account_col]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    # -------------------------------------------------------------------------
    # 1. GLOBAL FILTERS (Default to last 90 days)
    # -------------------------------------------------------------------------
    max_db_date = df[date_col].max().date() if not df.empty else datetime.now().date()
    default_start = max_db_date - timedelta(days=90)

    with st.container():
        f1, f2 = st.columns(2)
        with f1:
            date_range = st.date_input(
                "Date Range",
                value=(default_start, max_db_date),
            )
        with f2:
            account_options = ["All Accounts"]
            if account_col in df.columns:
                account_options += sorted([a for a in df[account_col].unique() if a])
            selected_account = st.selectbox("Account", account_options)

    # Filter DataFrame by date range & account
    filtered_df = df.copy()

    filter_start_date, filter_end_date = None, None
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        filter_start_date, filter_end_date = date_range
        filtered_df = filtered_df[
            (filtered_df[date_col].dt.date >= filter_start_date)
            & (filtered_df[date_col].dt.date <= filter_end_date)
        ]

    if selected_account != "All Accounts" and account_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[account_col] == selected_account]

    if filtered_df.empty:
        st.info("No transactions match the selected filters.")
        return

    # Helper column for monthly grouping
    filtered_df["month_str"] = filtered_df[date_col].dt.strftime("%Y-%m")

    # Determine current / active ongoing months
    current_months = set()
    current_months.add(datetime.now().strftime("%Y-%m"))
    if max_db_date:
        current_months.add(max_db_date.strftime("%Y-%m"))
    if filter_end_date:
        current_months.add(filter_end_date.strftime("%Y-%m"))

    valid_months = set()

    for month in filtered_df["month_str"].unique():
        if month in current_months:
            valid_months.add(month)
            continue

        try:
            m_year, m_month = map(int, month.split("-"))
            m_start_date = date(m_year, m_month, 1)
            m_last_day = calendar.monthrange(m_year, m_month)[1]
            m_end_date = date(m_year, m_month, m_last_day)

            if filter_start_date and filter_end_date:
                if (filter_start_date <= m_start_date) and (filter_end_date >= m_end_date):
                    valid_months.add(month)
            else:
                valid_months.add(month)
        except ValueError:
            continue

    filtered_df = filtered_df[filtered_df["month_str"].isin(valid_months)]

    if filtered_df.empty:
        st.info("No full-month or current-month transactions match the selected date range.")
        return

    # -------------------------------------------------------------------------
    # 2. HERO KPI CARDS
    # -------------------------------------------------------------------------
    total_inflow = filtered_df[filtered_df[amount_col] > 0][amount_col].sum()
    total_outflow = filtered_df[filtered_df[amount_col] < 0][amount_col].sum()
    total_netflow = total_inflow + total_outflow

    num_months = max(1, filtered_df["month_str"].nunique())
    avg_inflow = total_inflow / num_months
    avg_outflow = total_outflow / num_months
    avg_netflow = total_netflow / num_months

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total In-Flow", f"${total_inflow:,.2f}")
    k2.metric("Total Out-Flow", f"${total_outflow:,.2f}")
    k3.metric("Total Net-Flow", f"${total_netflow:,.2f}")
    k4.metric("Avg In-Flow", f"${avg_inflow:,.2f}")
    k5.metric("Avg Out-Flow", f"${avg_outflow:,.2f}")
    k6.metric("Avg Net-Flow", f"${avg_netflow:,.2f}")

    st.divider()

    # -------------------------------------------------------------------------
    # 3. MONTHLY NET CASH FLOW CHART
    # -------------------------------------------------------------------------
    st.subheader("Monthly Net Cash Flow")

    monthly_summary = (
        filtered_df.groupby("month_str")
        .apply(
            lambda g: pd.Series(
                {
                    "In-Flow": g[g[amount_col] > 0][amount_col].sum(),
                    "Out-Flow": g[g[amount_col] < 0][amount_col].sum(),
                    "Net-Flow": g[amount_col].sum(),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )

    fig_cashflow = go.Figure()

    fig_cashflow.add_trace(
        go.Bar(
            x=monthly_summary["month_str"],
            y=monthly_summary["In-Flow"],
            name="In-Flow",
            marker_color="#10b981",
            hovertemplate="<b>In-Flow (%{x})</b>: $%{y:,.2f}<extra></extra>",
        )
    )
    fig_cashflow.add_trace(
        go.Bar(
            x=monthly_summary["month_str"],
            y=monthly_summary["Net-Flow"],
            name="Net-Flow",
            marker_color="#3b82f6",
            hovertemplate="<b>Net-Flow (%{x})</b>: $%{y:,.2f}<extra></extra>",
        )
    )
    fig_cashflow.add_trace(
        go.Bar(
            x=monthly_summary["month_str"],
            y=monthly_summary["Out-Flow"],
            name="Out-Flow",
            marker_color="#ef4444",
            hovertemplate="<b>Out-Flow (%{x})</b>: $%{y:,.2f}<extra></extra>",
        )
    )

    fig_cashflow.update_layout(
        barmode="group",
        bargap=0.25,
        bargroupgap=0.08,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title="Month",
            type="category",
            showgrid=False,
            tickfont=dict(size=12),
        ),
        yaxis=dict(
            title="Amount ($)",
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.1)",
            zerolinecolor="rgba(255, 255, 255, 0.2)",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=20, r=20, t=30, b=20),
        height=420,
    )

    st.plotly_chart(fig_cashflow, use_container_width=True)

    # -------------------------------------------------------------------------
    # 4. INCOME REPORT (DYNAMIC DB RULES & SUBCATEGORY MATCHING)
    # -------------------------------------------------------------------------
    with st.expander("🔻 Income Report", expanded=True):
        inflows_df = filtered_df[filtered_df[amount_col] > 0].copy()

        # Direct exact subcategory match
        is_payroll_subcat = inflows_df[subcat_col].str.strip().str.lower() == "payroll & direct deposit"

        # Exclude internal account transfers from other income calculations
        is_account_transfer = (
            (inflows_df[category_col].str.strip().str.lower() == "financial & transfers")
            & (inflows_df[subcat_col].str.strip().str.lower() == "account transfer")
        )

        # Query database categorization rules dynamically
        try:
            rules_data = get_all_rules()
        except Exception:
            rules_data = []

        payroll_patterns = []
        if isinstance(rules_data, pd.DataFrame) and not rules_data.empty:
            p_rules = rules_data[
                rules_data["target_subcategory"].astype(str).str.strip() == "Payroll & Direct Deposit"
            ]
            payroll_patterns = [p for p in p_rules["pattern"].dropna().tolist() if p]
        elif isinstance(rules_data, list):
            for r in rules_data:
                target_sub = r.get("target_subcategory") if isinstance(r, dict) else getattr(r, "target_subcategory", None)
                pattern_val = r.get("pattern") if isinstance(r, dict) else getattr(r, "pattern", None)
                if str(target_sub).strip() == "Payroll & Direct Deposit" and pattern_val:
                    payroll_patterns.append(pattern_val)

        if payroll_patterns:
            regex_rule_pattern = "|".join([re.escape(p) for p in payroll_patterns])
            is_payroll_rule = inflows_df[desc_col].str.contains(
                regex_rule_pattern, case=False, na=False
            ) | inflows_df[category_col].str.contains(
                regex_rule_pattern, case=False, na=False
            )
        else:
            is_payroll_rule = pd.Series(False, index=inflows_df.index)

        is_payroll = is_payroll_subcat | is_payroll_rule

        payroll_df = inflows_df[is_payroll]
        other_incomes_df = inflows_df[~is_payroll & ~is_account_transfer]

        ic1, ic2 = st.columns([1, 2])
        with ic1:
            payroll_total = payroll_df[amount_col].sum() if not payroll_df.empty else 0.0
            other_total = other_incomes_df[amount_col].sum() if not other_incomes_df.empty else 0.0

            st.metric("Total Payroll Income", f"${payroll_total:,.2f}")
            st.metric("Other Incomes", f"${other_total:,.2f}")

        with ic2:
            st.write("**Other Inflows Detail**")
            if not other_incomes_df.empty:
                cols_to_show = [
                    c for c in [date_col, merchant_col, desc_col, category_col, subcat_col, amount_col]
                    if c in other_incomes_df.columns
                ]

                column_rename_map = {
                    date_col: "Date",
                    merchant_col: "Merchant",
                    desc_col: "Description",
                    category_col: "Category",
                    subcat_col: "Subcategory",
                    amount_col: "Amount",
                }

                display_df = (
                    other_incomes_df[cols_to_show]
                    .sort_values(date_col, ascending=False)
                    .rename(columns=column_rename_map)
                )

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                        "Amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
                    },
                )
            else:
                st.info("No other inflows found in selected date range.")

    st.divider()

    # -------------------------------------------------------------------------
    # 5. DYNAMIC MONTHLY BREAKDOWN EXPANDERS
    # -------------------------------------------------------------------------
    st.subheader("📅 Monthly Expense Breakdowns")

    unique_months = sorted(filtered_df["month_str"].unique(), reverse=True)

    for idx, month in enumerate(unique_months):
        month_data = filtered_df[filtered_df["month_str"] == month]
        m_inflow = month_data[month_data[amount_col] > 0][amount_col].sum()
        m_outflow = month_data[month_data[amount_col] < 0][amount_col].sum()

        with st.expander(
            f"Month: {month} -- Expense Report",
            expanded=(idx == 0),
        ):
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Selected Month", month)
            mc2.metric("Total Inflow", f"${m_inflow:,.2f}")
            mc3.metric("Total Outflow", f"${m_outflow:,.2f}")

            expenses_df = month_data[month_data[amount_col] < 0].copy()

            if not expenses_df.empty:
                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    st.write("**Expenses by Category**")
                    if category_col in expenses_df.columns:
                        cat_summary = (
                            expenses_df.groupby(category_col)[amount_col]
                            .sum()
                            .sort_values()
                            .head(10)
                            .reset_index()
                        )
                        cat_summary["Amount_Abs"] = cat_summary[amount_col].abs()

                        fig_cat = px.bar(
                            cat_summary,
                            x=category_col,
                            y="Amount_Abs",
                            text_auto=".2s",
                            color=category_col,
                            color_discrete_sequence=px.colors.qualitative.Bold,
                        )
                        fig_cat.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            showlegend=False,
                            xaxis_title="",
                            yaxis_title="Expense ($)",
                        )
                        st.plotly_chart(fig_cat, use_container_width=True)

                with chart_col2:
                    st.write("**Expenses by Merchant**")
                    target_m_col = merchant_col if (
                        merchant_col in expenses_df.columns
                        and expenses_df[merchant_col].str.strip().str.len().gt(0).any()
                    ) else desc_col

                    merch_summary = (
                        expenses_df.groupby(target_m_col)[amount_col]
                        .sum()
                        .sort_values()
                        .head(10)
                        .reset_index()
                    )
                    merch_summary["Amount_Abs"] = merch_summary[amount_col].abs()

                    fig_merch = px.bar(
                        merch_summary,
                        x=target_m_col,
                        y="Amount_Abs",
                        text_auto=".2s",
                        color=target_m_col,
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                    )
                    fig_merch.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        xaxis_title="",
                        yaxis_title="Expense ($)",
                    )
                    st.plotly_chart(fig_merch, use_container_width=True)
            else:
                st.info("No expense transactions recorded for this month.")
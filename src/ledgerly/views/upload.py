import asyncio
import pandas as pd
import streamlit as st
from ledgerly.db.queries import delete_transactions_by_ids


def render(runner):
    st.title("📑 Upload CSV")

    # ------------------------------------------------------------------
    # 1. State Initialization
    # ------------------------------------------------------------------
    if "success_msg" not in st.session_state:
        st.session_state.success_msg = None
    if "info_msg" not in st.session_state:
        st.session_state.info_msg = None
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    if "last_processed_filename" not in st.session_state:
        st.session_state.last_processed_filename = None
    if "last_inserted_ids" not in st.session_state:
        st.session_state.last_inserted_ids = []
    if "cancel_requested" not in st.session_state:
        st.session_state.cancel_requested = False

    # ------------------------------------------------------------------
    # 2. Form Inputs (Two-Column Layout)
    # ------------------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        bank_name = st.selectbox(
            "Bank Name", ["TD Bank", "Chase", "Capital One", "Discover"]
        )

    with col2:
        account_type = st.selectbox(
            "Account Type", ["Checking", "Savings", "Credit Card"]
        )

    uploaded_file = st.file_uploader(
        "Upload Bank CSV",
        type=["csv"],
        key=f"file_uploader_{st.session_state.uploader_key}",
    )

    # ------------------------------------------------------------------
    # 3. File Preview & Row Count Detection
    # ------------------------------------------------------------------
    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.last_processed_filename:
            st.session_state.success_msg = None
            st.session_state.info_msg = None

        try:
            df_preview = pd.read_csv(uploaded_file)
            row_count = len(df_preview)
            uploaded_file.seek(0)
            st.info(
                f"File selected: **{uploaded_file.name}** ({row_count:,} rows ready to process)"
            )
        except Exception:
            st.info(f"File selected: **{uploaded_file.name}**")

    # ------------------------------------------------------------------
    # 4. Action Toolbar
    # ------------------------------------------------------------------
    run_disabled = uploaded_file is None
    cancel_disabled = run_disabled and not st.session_state.last_inserted_ids

    btn_col1, btn_col2 = st.columns([1, 1])

    with btn_col1:
        run_clicked = st.button(
            "🚀 Run ETL Pipeline", disabled=run_disabled, use_container_width=True
        )

    with btn_col2:
        if st.button(
            "❌ Cancel Upload", disabled=cancel_disabled, use_container_width=True
        ):
            # Roll back last import if pressed post-run
            if st.session_state.last_inserted_ids:
                deleted_count = delete_transactions_by_ids(
                    st.session_state.last_inserted_ids
                )
                st.session_state.last_inserted_ids = []
                st.session_state.success_msg = None
                st.session_state.info_msg = (
                    f"↩️ Upload cancelled! Removed **{deleted_count}** inserted transactions."
                )
            else:
                st.session_state.cancel_requested = True
                st.session_state.info_msg = (
                    "Upload cancelled. 0 rows were written to the database."
                )

            st.session_state.uploader_key += 1
            st.cache_data.clear()
            st.rerun()

    if not run_disabled:
        st.caption(
            f"ℹ️ Importing **{bank_name}** data into **{account_type}** account"
        )

    # ------------------------------------------------------------------
    # 5. Pipeline Execution
    # ------------------------------------------------------------------
    if run_clicked:
        st.session_state.cancel_requested = False
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(current: int, total: int):
            percent = min(int((current / total) * 100), 100) if total > 0 else 100
            progress_bar.progress(percent)
            status_text.caption(
                f"⏳ Processing transaction **{current}** of **{total}** ({percent}%)..."
            )

        def check_cancelled() -> bool:
            return st.session_state.cancel_requested

        try:
            uploaded_file.seek(0)

            result = asyncio.run(
                runner.run_pipeline(
                    file_stream=uploaded_file,
                    bank_name=bank_name,
                    account_type=account_type,
                    progress_callback=update_progress,
                    cancel_check=check_cancelled,
                )
            )

            progress_bar.empty()
            status_text.empty()

            if result.get("status") == "cancelled":
                st.session_state.info_msg = (
                    "Upload cancelled. 0 rows were written to the database."
                )
                st.session_state.success_msg = None
            else:
                added_count = result.get("processed_count", 0)
                skipped_count = result.get("skipped_count", 0)
                inserted_ids = result.get("inserted_ids", [])

                st.session_state.last_processed_filename = uploaded_file.name
                st.session_state.last_inserted_ids = inserted_ids
                st.session_state.info_msg = None
                st.session_state.success_msg = (
                    f"Pipeline complete! Successfully added **{added_count}** new transactions "
                    f"({skipped_count} duplicates skipped) to **{bank_name} ({account_type})**."
                )

            st.cache_data.clear()
            st.session_state.uploader_key += 1
            st.rerun()

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Pipeline execution failed: {e}")

    # ------------------------------------------------------------------
    # 6. Persistent Status Banners & Undo Control
    # ------------------------------------------------------------------
    if st.session_state.info_msg:
        st.info(st.session_state.info_msg)

    if st.session_state.success_msg:
        st.success(st.session_state.success_msg)

        if st.session_state.last_inserted_ids:
            if st.button(
                "↩️ Undo Last Import",
                help="Delete the transactions added in this batch",
                use_container_width=True,
            ):
                deleted_count = delete_transactions_by_ids(
                    st.session_state.last_inserted_ids
                )
                st.session_state.success_msg = None
                st.session_state.last_inserted_ids = []
                st.session_state.info_msg = (
                    f"↩️ Import rolled back! Removed **{deleted_count}** transactions from the database."
                )
                st.cache_data.clear()
                st.rerun()
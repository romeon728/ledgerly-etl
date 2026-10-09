import asyncio
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st
from ledgerly.db.queries import delete_transactions_by_ids


def save_artifact_file(file_bytes: bytes, original_filename: str, custom_name: str = None) -> Path:
    """Saves uploaded statement to persistent data/imports artifact store relative to project root."""
    # Anchors project_root to ledgerly-etl/ regardless of working directory
    project_root = Path(__file__).resolve().parents[2]  # Adjusts up from src/ledgerly/views/
    
    now = datetime.now()
    target_dir = project_root / "data" / "imports" / str(now.year) / f"{now.month:02d}"
    target_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(original_filename).suffix
    base_name = custom_name.strip() if custom_name and custom_name.strip() else Path(original_filename).stem
    
    safe_name = "".join(c for c in base_name if c.isalnum() or c in ("-", "_", " ")) + ext
    target_path = target_dir / safe_name

    if target_path.exists():
        target_path = target_dir / f"{target_path.stem}_{now.strftime('%H%M%S')}{ext}"

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    return target_path

def render(runner):
    st.title("📥 Import & Stage Bank Statement")

    if "success_msg" not in st.session_state:
        st.session_state.success_msg = None
    if "info_msg" not in st.session_state:
        st.session_state.info_msg = None
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    if "last_inserted_ids" not in st.session_state:
        st.session_state.last_inserted_ids = []
    if "staged_data" not in st.session_state:
        st.session_state.staged_data = None

    col1, col2 = st.columns(2)
    with col1:
        bank_name = st.selectbox("Bank Name", ["TD Bank", "Chase", "Capital One", "Discover"])
    with col2:
        account_type = st.selectbox("Account Type", ["Checking", "Savings", "Credit Card"])

    uploaded_file = st.file_uploader(
        "Upload Bank Statement",
        type=[
            "csv", 
            "text/csv", 
            "xlsx", 
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel"
        ],
        key=f"file_uploader_{st.session_state.uploader_key}",
    )

    custom_artifact_name = ""
    if uploaded_file is not None:
        custom_artifact_name = st.text_input(
            "Artifact Storage Name (Optional)",
            value=Path(uploaded_file.name).stem,
            help="Rename before saving to data/imports/ repo."
        )

    run_disabled = uploaded_file is None
    btn_col1, btn_col2 = st.columns([1, 1])

    with btn_col1:
        run_clicked = st.button("⚙️ Process & Stage Data", disabled=run_disabled, use_container_width=True, type="primary")

    with btn_col2:
        if st.button("❌ Clear Staging", disabled=st.session_state.staged_data is None, use_container_width=True):
            st.session_state.staged_data = None
            st.session_state.info_msg = "Staging cleared."
            st.rerun()

    # ------------------------------------------------------------------
    # Step 1: Stage Data (No Files Saved & No DB Writes)
    # ------------------------------------------------------------------
    if run_clicked and uploaded_file is not None:
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(current: int, total: int):
            percent = min(int((current / total) * 100), 100) if total > 0 else 100
            progress_bar.progress(percent)
            status_text.caption(f"⏳ Processing row **{current}** of **{total}** ({percent}%)...")

        try:
            # Capture file bytes in memory (DO NOT save artifact yet)
            file_bytes = uploaded_file.getvalue()
            uploaded_file.seek(0)

            # Call STAGING method
            df_staged, existing_hashes = asyncio.run(
                runner.stage_pipeline(
                    file_stream=uploaded_file,
                    bank_name=bank_name,
                    account_type=account_type,
                    progress_callback=update_progress,
                )
            )

            progress_bar.empty()
            status_text.empty()

            if df_staged is not None and not df_staged.empty:
                df_staged["Import"] = ~df_staged["tx_hash"].isin(existing_hashes)
                df_staged["Status"] = df_staged["tx_hash"].apply(
                    lambda h: "⚠️ Existing Duplicate" if h in existing_hashes else "✨ New Row"
                )

                st.session_state.staged_data = {
                    "df": df_staged,
                    "file_bytes": file_bytes,
                    "original_filename": uploaded_file.name,
                    "custom_artifact_name": custom_artifact_name,
                    "bank_name": bank_name,
                    "account_type": account_type
                }
                st.session_state.info_msg = None
            else:
                st.warning("No transactions could be extracted from this file.")

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Staging failed: {e}")

    # ------------------------------------------------------------------
    # Step 2: Interactive Staging & Commit
    # ------------------------------------------------------------------
    if st.session_state.staged_data is not None:
        st.divider()
        st.subheader("🔍 Staging Preview & Row Selection")

        staged_info = st.session_state.staged_data
        df_staged = staged_info["df"]

        new_count = (df_staged["Status"] == "✨ New Row").sum()
        dup_count = (df_staged["Status"] == "⚠️ Existing Duplicate").sum()

        target_name = staged_info.get("custom_artifact_name") or staged_info.get("original_filename", "statement")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Rows", len(df_staged))
        m2.metric("New Rows", new_count)
        m3.metric("Duplicates", dup_count)
        m4.caption(f"Target Artifact:\n`{target_name}`")
        cols = ["Import", "Status"] + [c for c in df_staged.columns if c not in ["Import", "Status", "tx_hash"]]

        edited_df = st.data_editor(
            df_staged[cols],
            column_config={
                "Import": st.column_config.CheckboxColumn("Import?", default=True),
                "Status": st.column_config.TextColumn("Status", disabled=True),
                "amount": st.column_config.NumberColumn("Amount ($)", format="$%.2f"),
                "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            },
            disabled=[c for c in cols if c != "Import"],
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic"
        )

        final_to_import = edited_df[edited_df["Import"] == True]

        col_commit, col_discard = st.columns([0.4, 0.6])

        with col_commit:
            if st.button(f"💾 Commit {len(final_to_import)} Transactions to DB", type="primary", use_container_width=True):
                if not final_to_import.empty:
                    # 1. SAVE ARTIFACT NOW (Only upon explicit user commit)
                    saved_path = save_artifact_file(
                        file_bytes=staged_info["file_bytes"],
                        original_filename=staged_info.get("original_filename", "statement.csv"),
                        custom_name=staged_info.get("custom_artifact_name")
                    )

                    # 2. Write selected rows to PostgreSQL
                    inserted_ids = runner.commit_dataframe(
                        df=final_to_import.drop(columns=["Import", "Status"]),
                        bank_name=staged_info["bank_name"],
                        account_type=staged_info["account_type"]
                    )

                    st.session_state.last_inserted_ids = inserted_ids
                    st.session_state.success_msg = f"🎉 Successfully added **{len(inserted_ids)}** new transactions to DB! (Artifact saved to `{saved_path}`)"
                    st.session_state.staged_data = None
                    st.session_state.uploader_key += 1
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("No rows selected for import.")

        with col_discard:
            if st.button("Discard Staging Data", use_container_width=True):
                st.session_state.staged_data = None
                st.rerun()

    # Banner messaging
    if st.session_state.info_msg:
        st.info(st.session_state.info_msg)

    if st.session_state.success_msg:
        st.success(st.session_state.success_msg)

        if st.session_state.last_inserted_ids:
            if st.button("↩️ Undo Last Import", use_container_width=True):
                deleted_count = delete_transactions_by_ids(st.session_state.last_inserted_ids)
                st.session_state.success_msg = None
                st.session_state.last_inserted_ids = []
                st.session_state.info_msg = f"↩️ Import rolled back! Removed **{deleted_count}** transactions."
                st.cache_data.clear()
                st.rerun()
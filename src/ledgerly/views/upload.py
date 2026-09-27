import streamlit as st
import asyncio

def render(runner):
    st.subheader("Upload Bank Export")
    
    col1, col2 = st.columns(2)
    with col1:
        bank_name = st.selectbox("Bank Name", ["TD Bank", "Chase", "Capital One", "Other"])
    with col2:
        account_type = st.selectbox("Account Type", ["Checking", "Savings", "Credit"])
    
    uploaded_file = st.file_uploader("Upload Bank CSV", type=["csv"])
    
    if uploaded_file:
        st.info(f"File selected: **{uploaded_file.name}**")
        if st.button("🚀 Run ETL Pipeline", type="primary"):
            with st.spinner("Processing CSV, deduplicating, and running local vLLM inference..."):
                try:
                    result = asyncio.run(
                        runner.run_pipeline(
                            file_stream=uploaded_file,
                            bank_name=bank_name,
                            account_type=account_type
                        )
                    )
                    st.success(
                        f"Pipeline complete! Successfully added **{result['processed_count']}** new transactions "
                        f"({result['skipped_count']} duplicates skipped)."
                    )
                except Exception as e:
                    st.error(f"❌ ETL Pipeline failed: {e}")
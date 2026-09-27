import streamlit as st

def render():
    st.subheader("Grafana Analytics & Dashboard")
    st.markdown(
        """
        <style>
        .custom-link {
            text-decoration: none;
            color: #ff4b4b;
            font-weight: 600;
            font-size: 1.1rem;
        }
        .custom-link:hover {
            text-decoration: underline;
        }
        </style>
        <a class="custom-link" href="http://localhost:3000/d/adl5rnw/ledgerly?orgId=1&from=now-1y&to=now&timezone=browser&var-bank=TD%20Bank" target="_blank">
            🔗 Open Ledgerly Grafana Report
        </a>
        """,
        unsafe_allow_html=True
    )
    st.info("💡 Advanced Streamlit analytics and statistics coming soon!")
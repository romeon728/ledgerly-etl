import os
from pathlib import Path
import streamlit as st


def render():
    st.title("💡 About Ledgerly")

    # Search common root paths inside and outside the container
    possible_paths = [
        Path("/app/README.md"),
        Path(__file__).resolve().parents[3] / "README.md",
        Path("README.md").resolve(),
    ]

    readme_path = None
    for p in possible_paths:
        if p.exists() and p.is_file():
            readme_path = p
            break

    if readme_path:
        try:
            content = readme_path.read_text(encoding="utf-8")

            # Strip outer markdown code blocks if present
            cleaned = content.strip()
            if cleaned.startswith("```markdown"):
                cleaned = cleaned[11:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            st.markdown(cleaned.strip(), unsafe_allow_html=True)
            return
        except Exception as e:
            st.error(f"Error reading README file at `{readme_path}`: {e}")

    # Fallback status if README is still inaccessible
    st.warning("⚠️ Could not locate `README.md` inside the container environment.")
    st.markdown("### 📊 Ledgerly ETL & Dashboard")
    st.write(
        "Automated bank transaction ingestion powered by local vLLM inference and PostgreSQL."
    )
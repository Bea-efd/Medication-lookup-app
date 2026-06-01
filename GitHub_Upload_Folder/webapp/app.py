import sys
import os
import streamlit as st

# Add the desktop 'app' directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
desktop_app_dir = os.path.join(parent_dir, "app")

if desktop_app_dir not in sys.path:
    sys.path.insert(0, desktop_app_dir)

st.set_page_config(
    page_title="Medication Lookup",
    page_icon="💊",
    layout="wide"
)

st.title("💊 Medication Lookup")
st.markdown("""
Welcome to the web version of the Medication Lookup application.

Please use the sidebar to navigate between:
- **1. Single Lookup**: Search for individual medications.
- **2. Bulk Processing**: Upload an Excel/CSV file to process multiple medications at once.
- **3. Source Library**: View the underlying data sources.
""")

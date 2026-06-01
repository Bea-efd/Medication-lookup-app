import streamlit as st
import sys
import os
import pandas as pd

# Add the desktop 'app' directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
desktop_app_dir = os.path.join(parent_dir, "app")

if desktop_app_dir not in sys.path:
    sys.path.insert(0, desktop_app_dir)

from core.engine import LookupEngine

st.set_page_config(page_title="Single Lookup", page_icon="🔍")

st.title("🔍 Single Medication Lookup")
st.markdown("Search for a medication across all active sources.")

# Cache the engine to avoid repeatedly hitting the DB / file system unnecessarily
@st.cache_resource
def get_engine():
    return LookupEngine()

try:
    engine = get_engine()
except Exception as e:
    st.error(f"Failed to initialize Lookup Engine: {e}")
    st.stop()

# Inputs
col1, col2 = st.columns(2)
with col1:
    med_name = st.text_input("Medication Name", placeholder="e.g. Paracetamol")
with col2:
    dose = st.text_input("Dose", placeholder="e.g. 500mg")

allow_web = st.checkbox("Enable Web Search (Live BNF lookups)", value=True)

if st.button("Search", type="primary"):
    if not med_name:
        st.warning("Please enter a medication name.")
    else:
        with st.spinner("Searching active sources..."):
            try:
                results = engine.search_medication(med_name, dose, allow_web=allow_web)
                
                st.subheader("Results summary")
                st.markdown(f"**Searched For:** {results.get('medication')} {results.get('dose')}")
                st.markdown(f"**ATC Codes:** {results.get('atc_codes')}")
                st.markdown(f"**Sources Referenced:** {results.get('sources')}")
                
                st.subheader("Detailed Matches")
                matches = results.get("matches", [])
                if matches:
                    df = pd.DataFrame(matches)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No matching combinations found in the active sources.")
            except Exception as e:
                st.error(f"An error occurred during search: {e}")

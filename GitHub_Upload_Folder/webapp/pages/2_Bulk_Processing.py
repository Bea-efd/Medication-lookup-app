import streamlit as st
import pandas as pd
import sys
import os
import io

# Add the desktop 'app' directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
desktop_app_dir = os.path.join(parent_dir, "app")

if desktop_app_dir not in sys.path:
    sys.path.insert(0, desktop_app_dir)

from core.engine import LookupEngine

st.set_page_config(page_title="Bulk Processing", page_icon="📑")

st.title("📑 Bulk Processing")
st.markdown("Upload an Excel or CSV file containing a list of medications and doses to process them all at once.")

# Cache the engine
@st.cache_resource
def get_engine():
    # Instantiating a new engine forces it to read the latest active sources from DB
    return LookupEngine()

try:
    engine = get_engine()
except Exception as e:
    st.error(f"Failed to initialize Lookup Engine: {e}")
    st.stop()

uploaded_file = st.file_uploader("Upload Excel or CSV", type=['csv', 'xlsx', 'xls'])

if uploaded_file is not None:
    # Read the file
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    st.subheader("Data Preview")
    st.dataframe(df.head(5), use_container_width=True)

    # Detect Columns
    cols_lower = [str(c).lower().strip() for c in df.columns]
    med_col = None
    dose_col = None
    
    for i, col in enumerate(cols_lower):
        if "med" in col or "name" in col or "drug" in col:
            med_col = df.columns[i]
        if "dose" in col or "strength" in col:
            dose_col = df.columns[i]

    if not med_col or not dose_col:
        st.warning("Could not automatically identify 'Medication' and 'Dose' columns. Please select them manually.")
        col1, col2 = st.columns(2)
        with col1:
            med_col = st.selectbox("Select Medication Column", df.columns)
        with col2:
            dose_col = st.selectbox("Select Dose Column", df.columns)
    else:
        st.success(f"Detected columns - Medication: `{med_col}`, Dose: `{dose_col}`")

    allow_web = st.checkbox("Enable Web Search (Include active web links)", value=True)

    if st.button("Process File", type="primary"):
        with st.spinner("Processing rows... This may take a while depending on the number of rows."):
            processed_df = df.copy()
            
            # New columns
            processed_df["ATC Codes"] = ""
            processed_df["Price"] = ""
            processed_df["Formulation"] = ""
            processed_df["Active Ingredient"] = ""
            processed_df["Packet Size"] = ""
            processed_df["Source Citations"] = ""

            progress_bar = st.progress(0)
            status_text = st.empty()
            total_rows = len(df)

            for index, row in df.iterrows():
                med = str(row[med_col])
                dose = str(row[dose_col])
                
                status_text.text(f"Processing row {index + 1} of {total_rows}: {med} {dose}")
                
                if med.lower() != "nan" and dose.lower() != "nan":
                    try:
                        result = engine.search_medication(med, dose, allow_web=allow_web)
                        
                        processed_df.at[index, "ATC Codes"] = result.get("atc_codes", "")
                        
                        all_prices = []
                        all_forms = []
                        all_actives = []
                        all_sizes = []
                        for m in result.get("matches", []):
                            if m.get("price", "Not Found") != "Not Found":  all_prices.append(str(m["price"]))
                            if m.get("formulation", "Not Found") != "Not Found": all_forms.append(str(m["formulation"]))
                            if m.get("active_ingredient", "Not Found") != "Not Found": all_actives.append(str(m["active_ingredient"]))
                            if m.get("packet_size", "Not Found") != "Not Found": all_sizes.append(str(m["packet_size"]))
                            
                        processed_df.at[index, "Price"] = " | ".join(all_prices) if all_prices else "Not Found"
                        processed_df.at[index, "Formulation"] = " | ".join(all_forms) if all_forms else "Not Found"
                        processed_df.at[index, "Active Ingredient"] = " | ".join(all_actives) if all_actives else "Not Found"
                        processed_df.at[index, "Packet Size"] = " | ".join(all_sizes) if all_sizes else "Not Found"
                        processed_df.at[index, "Source Citations"] = result.get("sources", "")
                    except Exception as e:
                        processed_df.at[index, "Source Citations"] = f"Error: {str(e)}"
                
                progress_bar.progress((index + 1) / total_rows)
            
            status_text.text("Processing complete!")
            st.success("Successfully processed all rows.")
            
            st.subheader("Results Preview")
            st.dataframe(processed_df.head(15), use_container_width=True)
            
            # Prepare download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                processed_df.to_excel(writer, index=False)
            output.seek(0)
            
            st.download_button(
                label="📥 Download Results as Excel",
                data=output,
                file_name="Processed_Medications.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

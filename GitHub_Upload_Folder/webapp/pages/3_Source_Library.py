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

from database import get_db_session, SourceDocument

st.set_page_config(page_title="Source Library", page_icon="📚")

st.title("📚 Source Library")
st.markdown("View the underlying data sources configured for the medication lookup.")

try:
    session = get_db_session()
    sources = session.query(SourceDocument).all()
    session.close()

    if not sources:
        st.info("No sources found in the database.")
    else:
        data = []
        for s in sources:
            data.append({
                "Name": s.name,
                "Type": s.source_type.upper(),
                "Status": "✅ Active" if s.is_active else "❌ Inactive",
                "Date Added": s.added_date.strftime("%Y-%m-%d %H:%M") if s.added_date else "Unknown",
                "Location": s.url if s.source_type == 'link' else s.file_path
            })
            
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
    st.info("💡 **Note**: To add, edit, or remove sources, please continue to use the desktop application. This web interface provides safe, read-only access to the library to ensure your files and database remain perfectly synced.")
    
except Exception as e:
    st.error(f"Error connecting to database: {e}")

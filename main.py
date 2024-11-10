import streamlit as st
import plotly.express as px
from database import Database
from components.code_comparison import render_code_comparison
from components.visualizations import render_visualizations
from components.search import render_search
from components.update_tracker import render_update_tracker
from components.policy_recommendations import render_policy_recommendations
from utils.data_processing import process_code_differences
from utils.code_tracker import CodeTracker

# Page configuration
st.set_page_config(
    page_title="Building Code Analysis",
    page_icon="🏗️",
    layout="wide"
)

# Load custom CSS
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize database and code tracker
db = Database()
code_tracker = CodeTracker(db)

# Sidebar - Role Selection
st.sidebar.title("Building Code Analysis")
role = st.sidebar.selectbox(
    "Select Your Role",
    ["Architect", "Contractor", "Inspector", "Policy Maker"]  # Added Policy Maker role
)

# Main content
st.title("Building Code Analysis Platform")
st.markdown(f"Viewing as: **{role}**")

# Tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Code Search & Compare", 
    "Visualizations", 
    "Analysis", 
    "Updates",
    "Policy Recommendations"  # New tab
])

with tab1:
    # Search and jurisdiction selection
    selected_jurisdictions = render_search(db)
    
    # Code comparison
    if selected_jurisdictions:
        render_code_comparison(db, selected_jurisdictions)

with tab2:
    if selected_jurisdictions:
        render_visualizations(db, selected_jurisdictions)

with tab3:
    if selected_jurisdictions:
        st.subheader("Code Difference Analysis")
        
        codes = []
        for jurisdiction in selected_jurisdictions:
            jurisdiction_codes = db.get_building_codes(jurisdiction)
            codes.extend(jurisdiction_codes)
        
        differences = process_code_differences(codes)
        
        for diff in differences:
            with st.expander(f"{diff['category']} - Section {diff['section']} ({diff['severity']} severity)"):
                st.markdown(f"**Affected Jurisdictions:** {', '.join(diff['jurisdictions'])}")
                
                for jurisdiction in diff['jurisdictions']:
                    # Replace the next() call with a safer alternative
                    try:
                        jurisdiction_code = next(
                            code for code in codes
                            if code['jurisdiction'] == jurisdiction 
                            and code['category'] == diff['category']
                            and code['section'] == diff['section']
                        )
                        st.markdown(f"**{jurisdiction}:**")
                        st.markdown(jurisdiction_code['content'])
                    except StopIteration:
                        st.warning(f"No matching code found for {jurisdiction} in {diff['category']} section {diff['section']}")

with tab4:
    render_update_tracker(db, code_tracker)

with tab5:
    if role == "Policy Maker":  # Show recommendations for Policy Makers
        if selected_jurisdictions:
            render_policy_recommendations(db, selected_jurisdictions)
    else:
        st.info("Policy recommendations are available for Policy Maker role. Please switch roles to access this feature.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit • Blueprint-inspired design")

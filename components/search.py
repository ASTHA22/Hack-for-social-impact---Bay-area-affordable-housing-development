import streamlit as st

def render_search(db):
    st.subheader("Search Building Codes")
    
    search_term = st.text_input("Search term")
    selected_jurisdictions = st.multiselect(
        "Select Jurisdictions",
        options=db.get_jurisdictions(),
        default=db.get_jurisdictions()[:2]
    )
    
    if search_term:
        codes = []
        for jurisdiction in selected_jurisdictions:
            jurisdiction_codes = db.get_building_codes(jurisdiction)
            codes.extend([
                code for code in jurisdiction_codes
                if search_term.lower() in code['content'].lower()
            ])
        
        if codes:
            for code in codes:
                with st.expander(f"{code['jurisdiction']} - {code['category']} - Section {code['section']}"):
                    st.markdown(code['content'])
        else:
            st.info("No results found")
    
    return selected_jurisdictions

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.nlp_processor import BuildingCodeNLP, analyze_code_differences
from typing import List, Dict

def calculate_impact_score(differences: Dict) -> float:
    try:
        score = 0
        weights = {
            'similarity': 0.3,
            'requirements': 0.3,
            'measurements': 0.2,
            'terms': 0.1,
            'references': 0.1
        }
        
        # Similarity impact (0-30 points)
        similarity_impact = (1 - differences['similarity_score']) * 100 * weights['similarity']
        score += similarity_impact
        
        # Requirements impact (0-30 points)
        req_changes = differences['requirement_changes']
        total_req_changes = len(req_changes['added']) + len(req_changes['removed'])
        req_impact = min(100, total_req_changes * 20) * weights['requirements']
        score += req_impact
        
        # Measurements impact (0-20 points)
        measurements_diff = abs(
            len(differences['entities_code1']['measurements']) - 
            len(differences['entities_code2']['measurements'])
        )
        measurement_impact = min(100, measurements_diff * 25) * weights['measurements']
        score += measurement_impact
        
        # Technical terms impact (0-10 points)
        terms1 = set()
        terms2 = set()
        for term_group in differences['entities_code1']['technical_terms']:
            terms1.update(term_group.get('terms', []))
        for term_group in differences['entities_code2']['technical_terms']:
            terms2.update(term_group.get('terms', []))
        terms_diff = len(terms1.symmetric_difference(terms2))
        terms_impact = min(100, terms_diff * 15) * weights['terms']
        score += terms_impact

        # References impact (0-10 points)
        references1 = set(ref['text'] for ref in differences['entities_code1']['references'])
        references2 = set(ref['text'] for ref in differences['entities_code2']['references'])
        ref_diff = len(references1.symmetric_difference(references2))
        ref_impact = min(100, ref_diff * 15) * weights['references']
        score += ref_impact
        
        return min(100, max(0, score))
    except Exception as e:
        print(f"Error calculating impact score: {e}")
        return 50  # Default moderate impact

def analyze_citations(differences: Dict, jurisdiction1: str, jurisdiction2: str) -> Dict:
    """Analyze citations and references between codes"""
    references1 = differences['entities_code1']['references']
    references2 = differences['entities_code2']['references']
    
    citation_analysis = {
        'common_references': [],
        'unique_references': {jurisdiction1: [], jurisdiction2: []},
        'reference_types': {'section': 0, 'code': 0, 'external': 0},
        'cross_references': []
    }
    
    # Analyze common and unique references
    refs1 = {(ref['text'], ref['type']) for ref in references1}
    refs2 = {(ref['text'], ref['type']) for ref in references2}
    
    common_refs = refs1.intersection(refs2)
    unique_refs1 = refs1 - refs2
    unique_refs2 = refs2 - refs1
    
    citation_analysis['common_references'] = list(common_refs)
    citation_analysis['unique_references'][jurisdiction1] = list(unique_refs1)
    citation_analysis['unique_references'][jurisdiction2] = list(unique_refs2)
    
    # Count reference types
    all_refs = references1 + references2
    for ref in all_refs:
        citation_analysis['reference_types'][ref['type']] += 1
    
    return citation_analysis

def get_primary_action(differences: Dict, jurisdiction1: str, jurisdiction2: str) -> str:
    if len(differences['requirement_changes']['added']) > len(differences['requirement_changes']['removed']):
        return f"Focus on simplifying {jurisdiction2}'s additional requirements to match {jurisdiction1}'s standards"
    return f"Review {jurisdiction1}'s reduced requirements against {jurisdiction2}'s safety standards"

def get_secondary_action(differences: Dict, jurisdiction1: str, jurisdiction2: str) -> str:
    if len(differences['entities_code1']['measurements']) > len(differences['entities_code2']['measurements']):
        return f"Standardize measurement specifications between {jurisdiction1} and {jurisdiction2}"
    return f"Align technical terminology and definitions between jurisdictions"

def generate_recommendations(differences: Dict, jurisdiction1: str, jurisdiction2: str) -> List[Dict]:
    """Generate specific policy recommendations based on code differences"""
    try:
        recommendations = []
        citation_analysis = analyze_citations(differences, jurisdiction1, jurisdiction2)
        
        # Get specific technical differences
        tech_terms1 = set(term for group in differences['entities_code1']['technical_terms'] for term in group['terms'])
        tech_terms2 = set(term for group in differences['entities_code2']['technical_terms'] for term in group['terms'])
        different_terms = tech_terms1.symmetric_difference(tech_terms2)
        
        # Calculate specific impact areas
        requirement_differences = len(differences['requirement_changes']['added']) + len(differences['requirement_changes']['removed'])
        measurement_differences = abs(
            len(differences['entities_code1']['measurements']) - 
            len(differences['entities_code2']['measurements'])
        )
        
        # Create tailored recommendation
        recommendations.append({
            'category': 'Code Unification',
            'description': f'Specific recommendations for {jurisdiction1} and {jurisdiction2} code alignment',
            'impact': 'High' if requirement_differences > 5 else 'Medium',
            'benefit': f'Targeted improvements for {jurisdiction1}-{jurisdiction2} coordination',
            'details': [
                f"- Found {requirement_differences} different requirements between {jurisdiction1} and {jurisdiction2}",
                f"- {measurement_differences} measurement standard variations identified",
                f"- Key technical term differences: {', '.join(list(different_terms)[:5])}",
                f"- Estimated compliance cost reduction: {min(requirement_differences * 5, 30)}%",
                "Specific Actions:",
                "1. " + get_primary_action(differences, jurisdiction1, jurisdiction2),
                "2. " + get_secondary_action(differences, jurisdiction1, jurisdiction2)
            ],
            'citations': [
                f"- {jurisdiction1} Section {ref['text']}" for ref in differences['entities_code1']['references'][:3]
            ] + [
                f"- {jurisdiction2} Section {ref['text']}" for ref in differences['entities_code2']['references'][:3]
            ]
        })
        
        return recommendations
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return []

def render_policy_recommendations(db, selected_jurisdictions):
    """Render the policy recommendations interface with enhanced comparisons and citations"""
    try:
        st.title("Policy Recommendations")
        
        if len(selected_jurisdictions) < 2:
            st.warning("Please select at least two jurisdictions to generate recommendations")
            return
        
        # Get building codes for selected jurisdictions
        codes = []
        for jurisdiction in selected_jurisdictions:
            jurisdiction_codes = db.get_building_codes(jurisdiction)
            codes.extend(jurisdiction_codes)
        
        df = pd.DataFrame(codes)
        
        if df.empty:
            st.warning("No building codes found for the selected jurisdictions")
            return
        
        # Select category for analysis
        categories = sorted(df['category'].unique())
        selected_category = st.selectbox("Select Category for Analysis", categories)
        
        # Filter codes by category
        filtered_df = df[df['category'] == selected_category]
        
        # Analyze differences between jurisdictions
        st.subheader("Code Alignment Analysis")
        
        for i, jurisdiction1 in enumerate(selected_jurisdictions[:-1]):
            for jurisdiction2 in selected_jurisdictions[i+1:]:
                st.markdown(f"### {jurisdiction1} vs {jurisdiction2}")
                
                try:
                    # Get codes for comparison
                    codes1 = filtered_df[filtered_df['jurisdiction'] == jurisdiction1]
                    codes2 = filtered_df[filtered_df['jurisdiction'] == jurisdiction2]
                    
                    if codes1.empty or codes2.empty:
                        st.warning(f"Insufficient code content for comparison between {jurisdiction1} and {jurisdiction2}")
                        continue
                    
                    code1 = codes1.iloc[0]['content']
                    code2 = codes2.iloc[0]['content']
                    
                    if not code1 or not code2:
                        st.warning("Insufficient code content for comparison")
                        continue
                    
                    # Analyze differences
                    differences = analyze_code_differences(code1, code2)
                    
                    # Generate recommendations
                    recommendations = generate_recommendations(differences, jurisdiction1, jurisdiction2)
                    
                    # Display recommendations with citations
                    if recommendations:
                        st.markdown("#### Recommended Actions")
                        for rec in recommendations:
                            with st.expander(f"{rec['category']} - {rec['impact']} Impact"):
                                st.markdown(f"**Description:** {rec['description']}")
                                st.markdown(f"**Expected Benefit:** {rec['benefit']}")
                                
                                # Display details
                                st.markdown("**Details:**")
                                for detail in rec['details']:
                                    st.markdown(detail)
                                
                                # Display citations
                                if 'citations' in rec:
                                    st.markdown("**Supporting Citations:**")
                                    for citation in rec['citations']:
                                        st.markdown(f"📌 {citation}")
                                        
                except Exception as e:
                    st.error(f"Error analyzing codes: {e}")
                    continue
                    
    except Exception as e:
        st.error(f"Error in policy recommendations: {e}")
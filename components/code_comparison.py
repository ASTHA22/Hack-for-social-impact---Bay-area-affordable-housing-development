from typing import Dict, List, Tuple
import streamlit as st
from uagents import Agent, Context, Model
from uagents.query import query
import pandas as pd
import plotly.express as px

class CodeComparisonModel(Model):
    content1: str
    content2: str
    
class ComparisonResult(Model):
    similarity_score: float
    differences: List[str]
    technical_terms1: List[str]
    technical_terms2: List[str]
    common_terms: List[str]
    
class BuildingCodeAgent:
    def __init__(self):
        # Initialize fetch.ai agent with a specific name and secure key
        self.agent = Agent(
            name="building_code_analyzer",
            seed="your-secure-seed-here"  # Replace with a secure seed
        )
        
        @self.agent.on_query(model=CodeComparisonModel)
        async def analyze_codes(ctx: Context, sender: str, msg: CodeComparisonModel) -> ComparisonResult:
            # Implement the NLP analysis using fetch.ai's capabilities
            from fetchai.uagents.nlp import similarity, extract_entities, text_differences
            
            # Calculate similarity score
            similarity_score = await similarity(msg.content1, msg.content2)
            
            # Extract technical terms
            terms1 = await extract_entities(msg.content1, entity_type="TECHNICAL")
            terms2 = await extract_entities(msg.content2, entity_type="TECHNICAL")
            
            # Find common terms
            common_terms = list(set(terms1).intersection(set(terms2)))
            
            # Analyze differences
            differences = await text_differences(msg.content1, msg.content2)
            
            return ComparisonResult(
                similarity_score=similarity_score,
                differences=differences,
                technical_terms1=terms1,
                technical_terms2=terms2,
                common_terms=common_terms
            )

async def analyze_code_differences(code1: str, code2: str) -> Dict:
    """
    Analyze differences between two building codes using fetch.ai
    """
    agent = BuildingCodeAgent()
    
    # Create the comparison query
    query = query(
        model=CodeComparisonModel(
            content1=code1,
            content2=code2
        )
    )
    
    # Get the analysis result
    result = await agent.agent.query(query)
    
    return {
        'similarity_score': result.similarity_score,
        'differences': result.differences,
        'entities_code1': {
            'technical_terms': [{'terms': result.technical_terms1}]
        },
        'entities_code2': {
            'technical_terms': [{'terms': result.technical_terms2}]
        },
        'common_terms': result.common_terms
    }

        
        
def render_code_comparison(db, selected_jurisdictions):
    try:
        if len(selected_jurisdictions) < 2:
            st.warning("Please select at least two jurisdictions to compare")
            return

        # Get all codes for selected jurisdictions with proper error handling
        codes = []
        try:
            for jurisdiction in selected_jurisdictions:
                jurisdiction_codes = db.get_building_codes(jurisdiction)
                if jurisdiction_codes:
                    codes.extend(jurisdiction_codes)
        except Exception as e:
            st.error(f"Error fetching building codes: {e}")
            return

        if not codes:
            st.warning("No building codes found for the selected jurisdictions")
            return

        # Create DataFrame
        df = pd.DataFrame(codes)
        
        # Add timeline analysis first
        with st.expander("📅 Code Timeline Analysis", expanded=True):
            timeline_data = []
            for jurisdiction in selected_jurisdictions:
                jurisdiction_df = df[df['jurisdiction'] == jurisdiction]
                
                created_date = None
                updated_date = None
                
                try:
                    if 'created_at' in jurisdiction_df.columns:
                        created_date = pd.to_datetime(jurisdiction_df['created_at'].min())
                    if 'last_updated' in jurisdiction_df.columns:
                        updated_date = pd.to_datetime(jurisdiction_df['last_updated'].max())
                except Exception as e:
                    st.warning(f"Error processing dates for {jurisdiction}: {e}")
                    continue
                
                if created_date is not None:
                    timeline_data.append({
                        'jurisdiction': jurisdiction,
                        'start_date': created_date,
                        'end_date': updated_date if updated_date is not None else created_date,
                        'total_sections': len(jurisdiction_df),
                        'unique_categories': len(jurisdiction_df['category'].unique())
                    })

            if timeline_data:
                timeline_df = pd.DataFrame(timeline_data)
                timeline_df['duration'] = timeline_df['end_date'] - timeline_df['start_date']
                
                fig = px.timeline(
                    timeline_df,
                    x_start='start_date',
                    x_end='end_date',
                    y='jurisdiction',
                    title='Code Update Timeline by Jurisdiction',
                    color='jurisdiction',
                    hover_data=['total_sections', 'unique_categories']
                )
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Jurisdiction",
                    showlegend=True,
                    height=200,
                    margin=dict(t=30, b=0)
                )
                st.plotly_chart(fig)

                # Display adoption statistics
                st.markdown("### Adoption Statistics")
                cols = st.columns(len(selected_jurisdictions))
                for idx, (col, jurisdiction) in enumerate(zip(cols, selected_jurisdictions)):
                    with col:
                        st.metric(
                            jurisdiction,
                            f"{timeline_data[idx]['total_sections']} sections",
                            f"{timeline_data[idx]['unique_categories']} categories"
                        )

        # Add custom CSS for styling
        st.markdown("""
            <style>
            .comparison-card {
                background-color: white;
                padding: 1.2rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin: 1.2rem 0;
            }
            .citation-box {
                background-color: #f8f9fa;
                border-left: 4px solid #0B5394;
                padding: 0.8rem 1rem;
                margin: 0.8rem 0;
                border-radius: 0 4px 4px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .recommendation-box {
                background-color: #e7f5ff;
                border: 1px solid #0B5394;
                border-radius: 5px;
                padding: 1.2rem;
                margin: 1rem 0;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            }
            .technical-term {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 4px;
                padding: 0.3rem 0.6rem;
                margin: 0.2rem;
                display: inline-block;
                font-size: 0.9rem;
            }
            .comparison-header {
                background-color: #0B5394;
                color: white;
                padding: 0.8rem;
                border-radius: 4px;
                margin: 1rem 0;
            }
            .evidence-section {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 1rem;
                margin: 0.5rem 0;
            }
            .impact-score {
                font-size: 1.2rem;
                font-weight: bold;
                color: #0B5394;
                text-align: center;
                padding: 1rem;
                background-color: #f8f9fa;
                border-radius: 4px;
                margin: 1rem 0;
            }
            </style>
        """, unsafe_allow_html=True)

        # Category and section selection
        categories = sorted(df['category'].unique())
        selected_category = st.selectbox("Select Category", categories)

        filtered_df = df[df['category'] == selected_category]
        sections = sorted(filtered_df['section'].unique())
        selected_section = st.selectbox("Select Section", sections)

        # Filter codes by selected section
        section_codes = filtered_df[filtered_df['section'] == selected_section]

        # Main comparison layout

        
        col1, col2 = st.columns(2)
        
        # Content column
        with col1:
            st.markdown('<h3 class="comparison-header">Code Content</h3>', unsafe_allow_html=True)
            
            comparison_codes = {}
            for jurisdiction in selected_jurisdictions:
                jurisdiction_code = section_codes[section_codes['jurisdiction'] == jurisdiction]
                if not jurisdiction_code.empty:
                    with st.expander(f"{jurisdiction} - Section {jurisdiction_code.iloc[0]['section']}", expanded=True):
                        code = jurisdiction_code.iloc[0]
                        st.markdown(f'<div class="citation-box">{code["content"]}</div>', unsafe_allow_html=True)
                        comparison_codes[jurisdiction] = {
                            'section': code['section'],
                            'content': code['content']
                        }
            st.markdown('</div>', unsafe_allow_html=True)

        # Analysis column
        with col2:            
            if len(comparison_codes) >= 2:
                jurisdictions = list(comparison_codes.keys())
                
                for i in range(len(jurisdictions)):
                    for j in range(i + 1, len(jurisdictions)):
                        jurisdiction1, jurisdiction2 = jurisdictions[i], jurisdictions[j]
                        
                        try:
                            code1 = comparison_codes[jurisdiction1]['content']
                            code2 = comparison_codes[jurisdiction2]['content']
        
                            # Use the new fetch.ai-based analysis
                            import asyncio
                            analysis = asyncio.run(analyze_code_differences(code1, code2))
                            
                            # Analyze differences
                            analysis = analyze_code_differences(code1, code2)
                            citation_analysis = analyze_citations(analysis, jurisdiction1, jurisdiction2)
                            recommendations = generate_recommendations(analysis, jurisdiction1, jurisdiction2)

                            st.markdown(f'<div class="comparison-header">{jurisdiction1} vs {jurisdiction2}</div>', 
                                      unsafe_allow_html=True)

                            # Technical Terms Analysis
                            with st.expander("🔍 Technical Terms Analysis", expanded=True):
                                terms1 = set()
                                terms2 = set()
                                for term_group in analysis['entities_code1']['technical_terms']:
                                    terms1.update(term_group['terms'])
                                for term_group in analysis['entities_code2']['technical_terms']:
                                    terms2.update(term_group['terms'])
                                
                                common_terms = terms1.intersection(terms2)
                                unique_terms1 = terms1 - terms2
                                unique_terms2 = terms2 - terms1
                                
                                if common_terms:
                                    st.markdown("**Common Technical Terms:**")
                                    st.markdown(" ".join([
                                        f'<span class="technical-term">{term}</span>'
                                        for term in common_terms
                                    ]), unsafe_allow_html=True)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if unique_terms1:
                                        st.markdown(f"**Unique to {jurisdiction1}:**")
                                        st.markdown(" ".join([
                                            f'<span class="technical-term">{term}</span>'
                                            for term in unique_terms1
                                        ]), unsafe_allow_html=True)
                                with col2:
                                    if unique_terms2:
                                        st.markdown(f"**Unique to {jurisdiction2}:**")
                                        st.markdown(" ".join([
                                            f'<span class="technical-term">{term}</span>'
                                            for term in unique_terms2
                                        ]), unsafe_allow_html=True)

                            # Citation Analysis
                            with st.expander("📚 Citation Analysis", expanded=True):
                                if citation_analysis['common_references']:
                                    st.markdown("**Common References:**")
                                    for ref_text, ref_type in citation_analysis['common_references']:
                                        st.markdown(f'<div class="citation-box">{ref_text} ({ref_type})</div>', 
                                                  unsafe_allow_html=True)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    unique_refs1 = citation_analysis['unique_references'][jurisdiction1]
                                    if unique_refs1:
                                        st.markdown(f"**Unique to {jurisdiction1}:**")
                                        for ref_text, ref_type in unique_refs1:
                                            st.markdown(f'<div class="citation-box">{ref_text} ({ref_type})</div>', 
                                                      unsafe_allow_html=True)
                                with col2:
                                    unique_refs2 = citation_analysis['unique_references'][jurisdiction2]
                                    if unique_refs2:
                                        st.markdown(f"**Unique to {jurisdiction2}:**")
                                        for ref_text, ref_type in unique_refs2:
                                            st.markdown(f'<div class="citation-box">{ref_text} ({ref_type})</div>', 
                                                      unsafe_allow_html=True)

                            # Unification Recommendations
                            with st.expander("🔄 Unification Recommendations", expanded=True):
                                for rec in recommendations:
                                    st.markdown(f'''
                                        <div class="recommendation-box">
                                            <h4>{rec['category']}</h4>
                                            <p><strong>Impact:</strong> {rec['impact']}</p>
                                            <p><strong>Benefit:</strong> {rec['benefit']}</p>
                                            <hr>
                                            <p>{rec['description']}</p>
                                            <div class="evidence-section">
                                                <h5>Supporting Evidence</h5>
                                                {"<br>".join(rec['citations'])}
                                                <h5>Detailed Analysis</h5>
                                                {"<br>".join(rec['details'])}
                                            </div>
                                        </div>
                                    ''', unsafe_allow_html=True)

                            # Impact Score and Similarity Gauge
                            impact_score = calculate_impact_score(analysis)
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(
                                    f'<div class="impact-score">Impact Score<br>{impact_score:.1f}/100</div>', 
                                    unsafe_allow_html=True
                                )
                            
                            with col2:
                                fig = go.Figure(go.Indicator(
                                    mode="gauge+number",
                                    value=analysis['similarity_score'] * 100,
                                    domain={'x': [0, 1], 'y': [0, 1]},
                                    title={'text': "Code Similarity"},
                                    gauge={
                                        'axis': {'range': [0, 100]},
                                        'bar': {'color': "#0B5394"},
                                        'steps': [
                                            {'range': [0, 33], 'color': "#FFE0E0"},
                                            {'range': [33, 66], 'color': "#FFF4E0"},
                                            {'range': [66, 100], 'color': "#E0FFE0"}
                                        ],
                                        'threshold': {
                                            'line': {'color': "#0B5394", 'width': 4},
                                            'thickness': 0.75,
                                            'value': analysis['similarity_score'] * 100
                                        }
                                    }
                                ))
                                fig.update_layout(height=200, margin=dict(t=30, b=0))
                                st.plotly_chart(fig)
                                
                        except Exception as e:
                            st.error(f"Error analyzing codes: {e}")
                            continue

            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"An error occurred: {e}")

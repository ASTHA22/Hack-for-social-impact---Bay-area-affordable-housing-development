import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def render_visualizations(db, selected_jurisdictions):
    st.subheader("Code Analysis Visualizations")
    
    # Get code data
    codes = []
    for jurisdiction in selected_jurisdictions:
        jurisdiction_codes = db.get_building_codes(jurisdiction)
        codes.extend(jurisdiction_codes)
    
    df = pd.DataFrame(codes)
    
    # Category distribution with proper grouping
    category_distribution = (
        df.groupby(['jurisdiction', 'category'], as_index=False)
        .agg(count=('id', 'count'))  # Count unique IDs
        .sort_values(['jurisdiction', 'category'])
    )
    
    fig_categories = px.bar(
        category_distribution,
        x='jurisdiction',
        y='count',
        color='category',
        title='Building Code Categories by Jurisdiction',
        labels={'count': 'Number of Sections', 'category': 'Category'}
    )
    st.plotly_chart(fig_categories, key="category_distribution")
    
    # Code complexity heatmap with deduplicated data
    complexity_data = (
        df.groupby(['jurisdiction', 'category'], as_index=False)
        .agg(complexity=('content', lambda x: len(' '.join(set(x)))))
    )  # Fixed missing parenthesis
    
    # Pivot the data for heatmap
    heatmap_data = complexity_data.pivot(
        index='jurisdiction',
        columns='category',
        values='complexity'
    )
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='Blues'
    ))
    fig_heatmap.update_layout(
        title='Code Complexity Heatmap',
        xaxis_title='Category',
        yaxis_title='Jurisdiction'
    )
    st.plotly_chart(fig_heatmap, key="complexity_heatmap")

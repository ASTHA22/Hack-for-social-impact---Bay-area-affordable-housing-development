import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.code_tracker import CodeTracker
import plotly.express as px

def render_update_tracker(db, code_tracker: CodeTracker):
    st.subheader("Code Update Tracking")
    
    # Create tabs for different tracking views
    tab1, tab2, tab3 = st.tabs(["Recent Updates", "Version History", "Update Notifications"])
    
    with tab1:
        st.markdown("### Recent Code Updates")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            jurisdiction = st.selectbox(
                "Select Jurisdiction",
                ["All"] + db.get_jurisdictions(),
                key="update_jurisdiction"
            )
        
        with col2:
            categories = ["All"] + sorted(set(
                code['category'] for code in db.get_building_codes()
            ))
            category = st.selectbox("Select Category", categories, key="update_category")
            
        with col3:
            timeframe = st.selectbox(
                "Timeframe",
                ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                key="update_timeframe"
            )
        
        # Calculate date filter
        from_date = None
        if timeframe != "All time":
            days = int(timeframe.split()[1])
            from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Get updates based on filters
        updates = code_tracker.get_code_updates(
            jurisdiction=None if jurisdiction == "All" else jurisdiction,
            category=None if category == "All" else category,
            from_date=from_date
        )
        
        if updates:
            updates_df = pd.DataFrame(updates)
            updates_df['update_date'] = pd.to_datetime(updates_df['update_date'])
            
            # Display updates in an expandable format
            for _, update in updates_df.iterrows():
                with st.expander(
                    f"{update['jurisdiction']} - {update['category']} - {update['section']} "
                    f"({update['change_type']} on {update['update_date'].strftime('%Y-%m-%d')})"
                ):
                    if update['change_type'] == 'MODIFY':
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Previous Version:**")
                            st.markdown(update['previous_content'])
                        with col2:
                            st.markdown("**New Version:**")
                            st.markdown(update['new_content'])
                    else:
                        st.markdown("**Content:**")
                        st.markdown(update['new_content'])
        else:
            st.info("No updates found for the selected filters")
    
    with tab2:
        st.markdown("### Version History")
        
        # Get all versions for each jurisdiction
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT jurisdiction, version_number, effective_date, created_at
                    FROM code_versions
                    ORDER BY jurisdiction, effective_date DESC
                """)
                versions = cur.fetchall()
        
        if versions:
            versions_df = pd.DataFrame(versions, columns=['Jurisdiction', 'Version', 'Effective Date', 'Created At'])
            versions_df['Effective Date'] = pd.to_datetime(versions_df['Effective Date'])
            versions_df['Created At'] = pd.to_datetime(versions_df['Created At'])
            
            st.dataframe(versions_df)
            
            # Version timeline visualization
            st.markdown("#### Version Timeline")
            
            fig = px.timeline(
                versions_df,
                x_start='Effective Date',
                x_end='Created At',
                y='Jurisdiction',
                color='Version',
                title='Code Version Timeline by Jurisdiction'
            )
            st.plotly_chart(fig, key="version_timeline")
        else:
            st.info("No version history available")
    
    with tab3:
        st.markdown("### Update Notifications")
        
        # Subscription form
        with st.form("subscription_form"):
            email = st.text_input("Email Address")
            sub_jurisdiction = st.selectbox("Jurisdiction", db.get_jurisdictions())
            sub_category = st.selectbox("Category (Optional)", ["All"] + sorted(set(
                code['category'] for code in db.get_building_codes()
            )))
            
            if st.form_submit_button("Subscribe to Updates"):
                if email and "@" in email:
                    category = None if sub_category == "All" else sub_category
                    sub_id = code_tracker.subscribe_to_updates(email, sub_jurisdiction, category)
                    if sub_id:
                        st.success("Successfully subscribed to updates!")
                    else:
                        st.info("You're already subscribed to these updates")
                else:
                    st.error("Please enter a valid email address")
        
        # Display current subscriptions
        if 'email' in locals() and email:
            st.markdown("#### Your Current Subscriptions")
            subscriptions = code_tracker.get_subscriptions(email)
            if subscriptions:
                subs_df = pd.DataFrame(subscriptions)
                st.dataframe(subs_df[['jurisdiction', 'category', 'created_at']])
            else:
                st.info("You don't have any active subscriptions")

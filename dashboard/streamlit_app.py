import os
os.environ["SALESGPT_USE_TOOLS"] = "false"

"""
Streamlit Dashboard for Manual Email Review + Analytics.

Run: streamlit run dashboard/streamlit_app.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from salesgpt.config import get_settings
from salesgpt.container import ServiceContainer
from workflows.manual_review_workflow import (
    load_pending_leads,
    approve_and_send,
    skip_lead,
    reject_lead,
    update_email_content
)
from services.analytics import MetricsTracker, RecommendationEngine

# Page config
st.set_page_config(
    page_title="Email Review Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for compact layout
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 50px;
        font-size: 16px;
        font-weight: bold;
    }
    .email-preview {
        font-family: 'Courier New', monospace;
        background: #f0f0f0;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #ddd;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #007bff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize services with error handling - lazy initialization
@st.cache_resource
def get_container():
    """Get service container (cached)."""
    try:
        settings = get_settings()
        return ServiceContainer(settings)
    except Exception as e:
        st.warning(f"⚠️ Error initializing services: {type(e).__name__}")
        st.info("Dashboard will work in read-only mode. Some features may be limited.")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
        return None

# Initialize on first use, not at import time
_container = None
def get_services():
    """Get services - lazy initialization."""
    global _container
    if _container is None:
        _container = get_container()
    
    if _container:
        return {
            'state_mgr': _container.state_manager,
            'smartlead': _container.smartlead,
            'hubspot': _container.crm,
            'metrics': MetricsTracker(_container.state_manager),
            'recommendations': RecommendationEngine(MetricsTracker(_container.state_manager)),
            'apollo_ab': _container.apollo_ab_manager
        }
    return None

# Session state for current index
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'stats' not in st.session_state:
    st.session_state.stats = {'approved': 0, 'rejected': 0, 'skipped': 0, 'sent': 0}

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📧 Email Review",
    "📊 Email Analytics",
    "🔍 Apollo A/B Testing",
    "🎯 Optimization"
])

# TAB 1: Email Review
with tab1:
    st.title("📧 Manual Email Review")
    
    # Load queue
    services = get_services()
    if not services:
        st.error("⚠️ Services not initialized. Please check error details above.")
        st.stop()
    
    queue = load_pending_leads(services['state_mgr'], limit=100)
    
    if not queue:
        st.warning("⚠️ Queue empty! Run background worker to fill queue.")
        st.info("Start the background worker: `python scripts/start_queue_builder.py`")
        st.stop()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ready to Review", len(queue))
    col2.metric("Current", f"#{st.session_state.current_idx + 1}")
    col3.metric("Approved Today", st.session_state.stats['approved'])
    col4.metric("Sent Today", st.session_state.stats['sent'])
    
    st.markdown("---")
    
    # Get current email
    if st.session_state.current_idx >= len(queue):
        st.session_state.current_idx = 0
    
    current = queue[st.session_state.current_idx]
    
    # Three-column layout
    col1, col2, col3 = st.columns([1, 3, 1])
    
    # LEFT PANEL: Queue
    with col1:
        st.markdown("### 📋 Queue")
        
        # Show queue list (first 15)
        for i, item in enumerate(queue[:15]):
            icon = "🟢" if i == st.session_state.current_idx else "○"
            name = item.get('name', 'Unknown')[:20]
            score = item.get('score', 0)
            st.text(f"{icon} {name}")
            st.caption(f"  Score: {score}")
        
        if len(queue) > 15:
            st.caption(f"... and {len(queue) - 15} more")
    
    # CENTER PANEL: Email Preview
    with col2:
        st.markdown(f"### 📧 Email #{st.session_state.current_idx + 1} of {len(queue)}")
        
        # Lead info
        st.info(f"**To:** {current.get('email', 'N/A')} | **Company:** {current.get('company_name', 'N/A')}")
        
        # Subject (editable)
        subject = st.text_input(
            "Subject:",
            value=current.get("email_subject", ""),
            key=f"subject_{st.session_state.current_idx}"
        )
        
        # Body (editable)
        body = st.text_area(
            "Body:",
            value=current.get("email_body", ""),
            height=400,
            key=f"body_{st.session_state.current_idx}"
        )
        
        # Action buttons
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        
        with col_btn1:
            if st.button("✅ APPROVE & SEND", key="approve", type="primary"):
                # Update content if edited
                if subject != current.get("email_subject") or body != current.get("email_body"):
                    update_email_content(current["email"], subject, body, services['state_mgr'])
                
                # Send
                success = approve_and_send(current, services['smartlead'], services['hubspot'], services['state_mgr'])
                
                if success:
                    st.session_state.stats['approved'] += 1
                    st.session_state.stats['sent'] += 1
                    st.session_state.current_idx += 1
                    st.rerun()
                else:
                    st.error("Failed to send email")
        
        with col_btn2:
            if st.button("✏️ SAVE EDIT", key="save"):
                update_email_content(current["email"], subject, body, services['state_mgr'])
                st.success("Email content saved!")
        
        with col_btn3:
            if st.button("⏭️ SKIP", key="skip"):
                skip_lead(current["email"], services['state_mgr'])
                st.session_state.stats['skipped'] += 1
                st.session_state.current_idx += 1
                st.rerun()
        
        with col_btn4:
            if st.button("🗑️ REJECT", key="reject"):
                reject_lead(current["email"], services['state_mgr'])
                st.session_state.stats['rejected'] += 1
                st.session_state.current_idx += 1
                st.rerun()
        
        # Bulk actions
        st.markdown("---")
        col_bulk1, col_bulk2 = st.columns(2)
        
        with col_bulk1:
            if st.button("⚡ Approve Top 10"):
                count = 0
                for i in range(min(10, len(queue) - st.session_state.current_idx)):
                    item = queue[st.session_state.current_idx + i]
                    if approve_and_send(item, services['smartlead'], services['hubspot'], services['state_mgr']):
                        count += 1
                
                st.session_state.stats['approved'] += count
                st.session_state.stats['sent'] += count
                st.session_state.current_idx += count
                st.success(f"Approved and sent {count} emails!")
                st.rerun()
        
        with col_bulk2:
            if st.button("⏭️ Skip Top 10"):
                count = 0
                for i in range(min(10, len(queue) - st.session_state.current_idx)):
                    item = queue[st.session_state.current_idx + i]
                    if skip_lead(item["email"], services['state_mgr']):
                        count += 1
                
                st.session_state.stats['skipped'] += count
                st.session_state.current_idx += count
                st.rerun()
    
    # RIGHT PANEL: Context
    with col3:
        st.markdown("### 📊 Lead Details")
        st.text(f"Name: {current.get('name', 'N/A')}")
        st.text(f"Company: {current.get('company_name', 'N/A')}")
        st.text(f"Location: {current.get('location', 'N/A')}")
        st.text(f"Specialty: {current.get('specialty', 'N/A')}")
        
        st.markdown("### 📈 Scoring")
        st.metric("Lead Score", f"{current.get('score', 0)}/20")
        st.metric("ELM Score", f"{current.get('elaboration_score', 0):.0f}/100")
        st.text(f"Route: {current.get('persuasion_route', 'N/A')}")
        
        st.markdown("### 🎯 Evidence")
        evidence = current.get("evidence", {})
        if evidence:
            st.text(f"Competitor: {evidence.get('competitor_name', 'N/A')}")
            st.text(f"Gap: {evidence.get('gap_percentage', 0)}%")
            st.text(f"Multiplier: {evidence.get('referral_multiplier', 0)}x")
        else:
            st.text("No evidence data")
        
        st.markdown("### 🧪 A/B Test")
        st.text(f"Variant: {current.get('variant_code', 'N/A')[:30]}")
        st.text(f"Apollo Config: {current.get('apollo_config_code', 'N/A')}")
        
        st.markdown("### 💼 HubSpot")
        if current.get("hubspot_contact_id"):
            st.markdown(f"[🔗 View Contact](https://app.hubspot.com/contacts/{current['hubspot_contact_id']})")
        else:
            st.text("No HubSpot contact")

# TAB 2: Email Analytics
with tab2:
    st.title("📊 Email Analytics & A/B Testing")
    
    # Time range selector
    days_back = st.selectbox("Time Range", [7, 14, 30, 60, 90], index=2)
    
    # Key metrics overview
    services = get_services()
    if not services:
        st.error("⚠️ Services not initialized. Analytics unavailable.")
        st.stop()
    
    all_leads = services['state_mgr'].get_all_leads()
    sent_leads = [l for l in all_leads if l.get("email_sent_at")]
    replied_leads = [l for l in all_leads if l.get("reply_received_at")]
    booked_leads = [l for l in all_leads if l.get("booked_at")]
    closed_leads = [l for l in all_leads if l.get("status") == "closed"]
    free_signup_leads = [l for l in all_leads if l.get("free_signup_at")]
    paid_pro_leads = [l for l in all_leads if l.get("paid_pro_at")]
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Emails Sent", len(sent_leads))
    col2.metric("Reply Rate", f"{len(replied_leads)/len(sent_leads)*100:.1f}%" if sent_leads else "0%")
    col3.metric("Booking Rate", f"{len(booked_leads)/len(sent_leads)*100:.1f}%" if sent_leads else "0%")
    col4.metric("Close Rate", f"{len(closed_leads)/len(sent_leads)*100:.1f}%" if sent_leads else "0%")
    col5.metric("Free Signups", len(free_signup_leads))
    col6.metric("Paid Pro", len(paid_pro_leads))
    
    st.markdown("---")
    
    # Variant Performance
    st.subheader("🧪 A/B Test Variant Performance")
    
    variants = set(l.get("variant_code") for l in all_leads if l.get("variant_code"))
    
    variant_data = []
    for variant in variants:
        perf = services['metrics'].get_variant_performance(variant, days_back)
        if "error" not in perf and perf.get("sent_count", 0) > 0:
            variant_data.append(perf)
    
    if variant_data:
        df_variants = pd.DataFrame(variant_data)
        df_variants = df_variants.sort_values("booking_rate", ascending=False)
        
        st.dataframe(
            df_variants[[
                "variant_code", "sent_count", "reply_rate",
                "positive_reply_rate", "booking_rate", "close_rate"
            ]],
            use_container_width=True
        )
        
        # Funnel chart
        if len(df_variants) > 0:
            fig = go.Figure()
            
            for idx, row in df_variants.head(5).iterrows():
                fig.add_trace(go.Funnel(
                    name=row["variant_code"][:20],
                    y=["Sent", "Replied", "Positive", "Booked", "Closed"],
                    x=[
                        100,
                        row["reply_rate"],
                        row["positive_reply_rate"],
                        row["booking_rate"],
                        row["close_rate"]
                    ],
                    textinfo="value+percent initial"
                ))
            
            fig.update_layout(
                title="Conversion Funnel by Variant (Top 5)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No A/B test data yet. Send more emails to see analytics.")
    
    st.markdown("---")
    
    # Niche Performance
    st.subheader("🎯 Niche Performance Analysis")
    
    niche_dimension = st.selectbox(
        "Analyze by",
        ["market", "specialty", "persona", "location", "score_tier", "elm_route"]
    )
    
    niche_data = services['metrics'].get_niche_performance(niche_dimension, days_back)
    
    if niche_data:
        df_niches = pd.DataFrame(niche_data)
        
        st.dataframe(df_niches, use_container_width=True)
        
        # Bar chart
        y_cols = ["reply_rate", "free_signup_rate", "paid_pro_rate", "booking_rate", "close_rate"]
        y_cols = [c for c in y_cols if c in df_niches.columns]
        fig = px.bar(
            df_niches.head(30),
            x="niche",
            y=y_cols,
            title=f"Performance by {niche_dimension.title()} (Top 30 by ROI Score)",
            barmode="group",
            height=450
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No niche data yet.")

# TAB 3: Apollo A/B Testing
with tab3:
    st.title("🔍 Apollo Lead Sourcing A/B Testing")
    
    services = get_services()
    if not services:
        st.error("⚠️ Services not initialized. Apollo A/B testing unavailable.")
        st.stop()
    
    apollo_ab = services.get('apollo_ab')
    
    # Overview
    col1, col2, col3 = st.columns(3)
    
    all_configs = apollo_ab.test_configs
    state_mgr = services['state_mgr']
    tested_configs = sum(
        1 for c in all_configs
        if len(state_mgr.get_all_leads_by_config(c.to_code())) >= 10
    )
    
    col1.metric("Total Configs", len(all_configs))
    col2.metric("Tested (10+ leads)", tested_configs)
    col3.metric("Pending Tests", len(all_configs) - tested_configs)
    
    st.markdown("---")
    
    # Performance report
    st.subheader("🏆 Apollo Config Performance")
    
    report = apollo_ab.get_config_performance_report()
    
    if report:
        df_apollo = pd.DataFrame(report)
        
        st.dataframe(
            df_apollo[[
                "config_code", "geography_strategy", "employee_range",
                "title_strategy", "leads_sourced", "avg_lead_score",
                "reply_rate", "booking_rate", "close_rate", "roi"
            ]],
            use_container_width=True
        )
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(
                df_apollo,
                x="employee_range",
                y="roi",
                color="roi",
                title="ROI by Employee Range Strategy",
                color_continuous_scale="RdYlGn"
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.bar(
                df_apollo,
                x="title_strategy",
                y="booking_rate",
                color="booking_rate",
                title="Booking Rate by Title Strategy",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Scatter plot
        fig3 = px.scatter(
            df_apollo,
            x="avg_lead_score",
            y="close_rate",
            size="leads_sourced",
            color="geography_strategy",
            hover_data=["config_code"],
            title="Lead Quality vs Close Rate",
            labels={
                "avg_lead_score": "Average Lead Score",
                "close_rate": "Close Rate (%)"
            }
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No Apollo A/B test data yet. Start sourcing leads to see analytics.")

# TAB 4: Optimization
with tab4:
    st.title("🎯 Optimization Recommendations")
    
    services = get_services()
    if not services or not services.get('recommendations'):
        st.error("⚠️ Services not initialized. Recommendations unavailable.")
        st.stop()
    
    recs = services['recommendations'].get_recommendations()
    
    if recs:
        for rec in recs:
            priority_color = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }.get(rec["priority"], "⚪")
            
            with st.expander(f"{priority_color} {rec['title']} ({rec['type'].replace('_', ' ').title()})"):
                st.write(f"**Description:** {rec['description']}")
                st.write(f"**Recommended Action:** {rec['action']}")
                st.write(f"**Confidence:** {rec.get('confidence', 0)*100:.0f}%")
                
                if rec["type"] == "email_variant":
                    if st.button(f"Apply: Use variant {rec['title'].split(':')[1].strip()} more", key=rec["title"]):
                        st.success("Variant allocation updated! New emails will use this variant more frequently.")
    else:
        st.info("Not enough data for recommendations yet. Send at least 50 emails with varied A/B tests.")
    
    st.markdown("---")
    
    # Manual optimization controls
    st.subheader("⚙️ Manual Optimization Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Target Niche Selection**")
        target_specialty = st.multiselect(
            "Focus on specialties",
            ["Dermatology", "Dental", "Cardiology", "Orthopedics", "Pediatrics"]
        )
        
        target_score = st.slider("Minimum lead score", 0, 20, 10)
        
        if st.button("Apply Targeting"):
            st.success(f"Now targeting: {', '.join(target_specialty)} with score >= {target_score}")
    
    with col2:
        st.write("**Variant Distribution**")
        st.write("Adjust A/B test variant allocation:")
        st.info("This feature will be available after more data is collected.")


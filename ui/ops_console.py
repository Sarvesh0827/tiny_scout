"""
TinyScout Ops Console - Streamlit Dashboard
Beautiful observability interface for research pipeline monitoring.
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="TinyScout Ops Console",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful design (mimicking HTML dashboard)
<style>
    /* Minimalist Dark Theme */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    .block-container {
        padding-top: 2rem;
    }
    
    /* Stats cards - Flat Dark */
    .stat-card {
        background-color: #1c1c21;
        padding: 20px;
        border-radius: 4px;
        border: 1px solid #262730;
        text-align: center;
    }
    
    /* Event items */
    .event-item {
        padding: 12px 16px;
        border-left: 3px solid #3b82f6;
        background-color: #1c1c21;
        margin-bottom: 8px;
        border-radius: 4px;
        font-size: 14px;
        color: #e0e0e0;
    }
    
    .event-item-warn {
        border-left-color: #f59e0b;
        background-color: #2e2a20; /* Darker warning bg */
    }
    
    .event-item-error {
        border-left-color: #ef4444;
        background-color: #2e2020; /* Darker error bg */
    }
    
    /* Panel headers */
    .panel-header {
        background-color: transparent;
        color: #a0a0a0;
        padding: 10px 0;
        border-bottom: 1px solid #262730;
        font-size: 14px;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 16px;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
        margin-right: 4px;
        color: white;
    }
    
    .badge-tier-a { background-color: #064e3b; color: #6ee7b7; }
    .badge-tier-b { background-color: #78350f; color: #fcd34d; }
    .badge-tier-c { background-color: #374151; color: #d1d5db; }
    
    /* Streamlit overrides */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 600;
        color: #fafafa;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #a0a0a0;
    }
    
    /* Table Styling */
    thead tr th {
        background-color: #1c1c21 !important;
        color: #a0a0a0 !important;
    }
    
    tbody tr td {
        background-color: #0e1117 !important;
        color: #e0e0e0 !important;
        border-bottom: 1px solid #262730 !important;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE = "http://localhost:8001"

# Sidebar
with st.sidebar:
    st.markdown("### 🔍 TinyScout Ops Console")
    st.markdown("Real-time observability for research pipeline")
    st.markdown("---")
    
    # Fetch latest runs to set default
    @st.cache_data(ttl=10)
    def fetch_latest_run_id():
        try:
            response = requests.get(f"{API_BASE}/api/runs?limit=1")
            runs = response.json()
            if runs:
                return runs[0]['id']
            return "07610c82-9e33-4d3e-a036-52cac6b91d3d" # Fallback test ID
        except:
            return "07610c82-9e33-4d3e-a036-52cac6b91d3d"

    # Run ID input
    col_id, col_btn = st.columns([3, 1])
    with col_id:
        if 'run_id' not in st.session_state:
            st.session_state.run_id = fetch_latest_run_id()
            
        run_id = st.text_input(
            "Run ID",
            value=st.session_state.run_id,
            help="Enter the run ID to view details"
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Latest"):
            st.session_state.run_id = fetch_latest_run_id()
            st.rerun()
    
    # Filters
    st.markdown("### Filters")
    stage_filter = st.selectbox(
        "Stage",
        ["All", "planner", "web_agent", "retriever", "synthesizer"],
        index=0
    )
    
    level_filter = st.selectbox(
        "Level",
        ["All", "info", "warn", "error", "debug"],
        index=0
    )
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (10s)", value=False)
    
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")

# Main header
st.markdown("# 🔍 TinyScout Ops Console")
st.markdown("**Real-time observability for research pipeline**")
st.markdown("---")

# Fetch data
@st.cache_data(ttl=10)
def fetch_run_details(run_id):
    try:
        response = requests.get(f"{API_BASE}/api/runs/{run_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=10)
def fetch_events(run_id, stage=None, level=None):
    try:
        params = {}
        if stage and stage != "All":
            params['stage'] = stage
        if level and level != "All":
            params['level'] = level
        
        response = requests.get(f"{API_BASE}/api/runs/{run_id}/events", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return []

@st.cache_data(ttl=10)
def fetch_documents(run_id):
    try:
        response = requests.get(f"{API_BASE}/api/runs/{run_id}/documents")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return []

# Load data
run_data = fetch_run_details(run_id)
events_data = fetch_events(run_id, stage_filter, level_filter)
docs_data = fetch_documents(run_id)

# Check for errors
if "error" in run_data:
    st.error(f"❌ Failed to load run details: {run_data['error']}")
    st.info("💡 Make sure the API server is running: `./venv/bin/python3 ops_api.py`")
    st.stop()

# Stats cards
st.markdown("### 📊 Overview")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Run ID", run_data['id'][:8] + "...")

with col2:
    status = run_data.get('status', 'unknown')
    status_color = {
        'success': '🟢',
        'failed': '🔴',
        'insufficient_evidence': '🟡',
        'running': '🔵'
    }.get(status, '⚪')
    st.metric("Status", f"{status_color} {status}")

with col3:
    st.metric("Topic", run_data.get('topic', 'Unknown'))

with col4:
    st.metric("Documents", run_data.get('doc_count', 0))

with col5:
    st.metric("Selected", run_data.get('selected_count', 0))

st.markdown("---")

# Main content area
col_left, col_right = st.columns([1, 1])

# Left column: Events Timeline
with col_left:
    st.markdown('<div class="panel-header">📊 Events Timeline</div>', unsafe_allow_html=True)
    
    if not events_data:
        st.info("No events found for this run")
    else:
        # Display events
        for event in events_data:
            level = event.get('level', 'info')
            stage = event.get('stage', 'unknown')
            message = event.get('message', '')
            ts = event.get('ts', '')
            payload = event.get('payload')
            
            # Event styling based on level
            if level == 'error':
                event_class = 'event-item-error'
                icon = '❌'
            elif level == 'warn':
                event_class = 'event-item-warn'
                icon = '⚠️'
            else:
                event_class = 'event-item'
                icon = 'ℹ️'
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = ts
            
            # Display event
            with st.container():
                st.markdown(f"""
                <div class="{event_class}">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-weight: 600; text-transform: uppercase; font-size: 12px;">{icon} {stage}</span>
                        <span style="color: #718096; font-size: 12px;">{time_str}</span>
                    </div>
                    <div style="color: #4a5568; margin-bottom: 8px;">{message}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show payload if exists
                if payload:
                    with st.expander("📝 View Payload", expanded=False):
                        st.json(payload)

# Right column: Run Details
with col_right:
    st.markdown('<div class="panel-header">📝 Run Details</div>', unsafe_allow_html=True)
    
    st.markdown(f"**Research Goal:**")
    st.info(run_data.get('research_goal', 'N/A'))
    
    st.markdown(f"**Models:**")
    st.text(f"Planner: {run_data.get('planner_model', 'N/A')}")
    st.text(f"Analyzer: {run_data.get('analyzer_model', 'N/A')}")
    st.text(f"Synthesizer: {run_data.get('synthesizer_model', 'N/A')}")
    
    st.markdown(f"**Backend:**")
    st.text(f"Retriever: {run_data.get('retriever_backend', 'N/A')}")
    
    if run_data.get('error_message'):
        st.error(f"**Error:** {run_data['error_message']}")

st.markdown("---")

# Documents table (full width)
st.markdown('<div class="panel-header">📄 Documents Extracted</div>', unsafe_allow_html=True)

if not docs_data:
    st.info("No documents found for this run")
else:
    # Prepare dataframe
    df_data = []
    for doc in docs_data:
        tier = doc.get('tier', 'unknown')
        tier_badge = f'<span class="badge badge-tier-{tier.lower()}">{tier}</span>'
        
        method_badge = f'<span class="badge">{doc.get("retrieval_method", "N/A")}</span>'
        
        selected = '✅' if doc.get('selected') else '❌'
        
        df_data.append({
            'URL': doc.get('url', 'N/A')[:60] + '...',
            'Method': method_badge,
            'Tier': tier_badge,
            'Length': f"{doc.get('content_len', 0):,} chars",
            'Score': f"{doc.get('relevance_score', 0):.2f}" if doc.get('relevance_score') else 'N/A',
            'Selected': selected
        })
    
    df = pd.DataFrame(df_data)
    
    # Display as HTML table for better styling
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# Auto-refresh
if auto_refresh:
    import time
    time.sleep(10)
    st.rerun()

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: white; padding: 20px;">
    <p>🔍 TinyScout Ops Console | API: {API_BASE} | Run ID: {run_id[:8]}...</p>
</div>
""", unsafe_allow_html=True)

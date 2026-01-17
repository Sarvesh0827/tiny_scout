"""
Yutori Monitoring Dashboard - Streamlit UI
Scheduled monitoring with periodic updates and citations.
"""
import streamlit as st
import asyncio
import sys
import os
import pandas as pd
from datetime import datetime

# Ensure app is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.monitors import ScoutManager, Scout, ScoutUpdate
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="TinyScout Monitoring",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (matching main dashboard)
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        margin-bottom: 25px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .main-header h1 {
        color: #ffffff;
        font-size: 48px;
        margin-bottom: 12px;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .panel {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        padding: 25px;
        margin-bottom: 25px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .panel-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 18px 25px;
        border-radius: 12px;
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .update-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #43e97b;
        margin-bottom: 15px;
        color: white;
    }
    
    .update-card h4 {
        color: #4facfe;
        margin-bottom: 10px;
    }
    
    .citation {
        background: rgba(255, 255, 255, 0.1);
        padding: 8px 12px;
        border-radius: 6px;
        margin: 5px;
        display: inline-block;
        font-size: 12px;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        font-weight: 600;
        padding: 14px 35px;
        border-radius: 10px;
        border: none;
        font-size: 16px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📡 Yutori Monitoring")
    st.markdown("**Scheduled Research Updates**")
    st.markdown("---")
    
    mode = st.radio(
        "Mode",
        ["📋 View Scouts", "➕ Create Scout"],
        index=0
    )
    
    st.markdown("---")
    
    if st.button("🔄 Refresh All", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")

# Main header
st.markdown("""
<div class="main-header">
    <h1>📡 Yutori Monitoring</h1>
    <p>Scheduled research with automatic updates and citations</p>
</div>
""", unsafe_allow_html=True)

# Initialize manager
@st.cache_resource
def get_scout_manager():
    return ScoutManager()

manager = get_scout_manager()

# Mode: Create Scout
if mode == "➕ Create Scout":
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-header">➕ Create New Scout</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        monitor_query = st.text_area(
            "🎯 Monitoring Query",
            value="Monitor AI voice moderation industry for news, updates, and announcements",
            height=100,
            help="Natural language query for what to monitor"
        )
    
    with col2:
        frequency = st.selectbox(
            "⏰ Frequency",
            ["30 min", "1 hour", "6 hours", "12 hours", "Daily"],
            index=2
        )
        
        enhance = st.checkbox(
            "Enhance Query",
            value=True,
            help="Add monitoring-specific instructions"
        )
    
    # Convert frequency to minutes
    freq_map = {
        "30 min": 30,
        "1 hour": 60,
        "6 hours": 360,
        "12 hours": 720,
        "Daily": 1440
    }
    interval_minutes = freq_map[frequency]
    
    if st.button("🚀 Start Monitoring", type="primary", use_container_width=True):
        with st.spinner("Creating scout..."):
            try:
                async def create():
                    scout = await manager.create_scout(
                        query=monitor_query,
                        interval_minutes=interval_minutes,
                        enhance_query=enhance
                    )
                    return scout
                
                scout = asyncio.run(create())
                
                st.success(f"✅ Scout created successfully!")
                st.info(f"**Scout ID:** `{scout.id}`")
                st.info(f"**Next Run:** {scout.next_run_timestamp}")
                
                # Switch to view mode
                st.session_state['mode'] = "📋 View Scouts"
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Failed to create scout: {e}")
                st.info("💡 Make sure YUTORI_API_KEY is set in .env")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Mode: View Scouts
else:
    # Get all scouts
    scouts = manager.get_all_scouts()
    
    if not scouts:
        st.info("📭 No active scouts. Create one to start monitoring!")
    else:
        # Display scouts
        for scout in scouts:
            with st.expander(f"📡 {scout.original_query[:60]}... (ID: {scout.id[:8]})", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Interval", f"{scout.output_interval // 60} min")
                
                with col2:
                    next_run = scout.next_run_timestamp
                    if next_run:
                        st.metric("Next Run", next_run.strftime("%H:%M"))
                    else:
                        st.metric("Next Run", "Unknown")
                
                with col3:
                    updates = manager.get_scout_updates(scout.id)
                    st.metric("Updates", len(updates))
                
                with col4:
                    st.metric("Status", "🟢 Active" if scout.is_active else "🔴 Inactive")
                
                # Action buttons
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    if st.button(f"🔄 Fetch Updates", key=f"fetch_{scout.id}"):
                        with st.spinner("Fetching updates..."):
                            try:
                                async def fetch():
                                    return await manager.fetch_updates(scout.id)
                                
                                new_updates = asyncio.run(fetch())
                                st.success(f"✅ Fetched {len(new_updates)} new updates")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                
                with col_b:
                    if st.button(f"📊 View Updates", key=f"view_{scout.id}"):
                        st.session_state[f'show_updates_{scout.id}'] = True
                
                with col_c:
                    if st.button(f"🗑️ Delete", key=f"delete_{scout.id}"):
                        if st.confirm(f"Delete scout {scout.id[:8]}?"):
                            async def delete():
                                return await manager.delete_scout(scout.id)
                            
                            success = asyncio.run(delete())
                            if success:
                                st.success("✅ Scout deleted")
                                st.rerun()
                
                # Show updates if requested
                if st.session_state.get(f'show_updates_{scout.id}', False):
                    st.markdown("---")
                    st.markdown("### 📰 Updates")
                    
                    updates = manager.get_scout_updates(scout.id, limit=20)
                    
                    if not updates:
                        st.info("No updates yet. Click 'Fetch Updates' to check for new content.")
                    else:
                        for update in updates:
                            st.markdown(f"""
                            <div class="update-card">
                                <h4>{update.headline or 'Update'}</h4>
                                <p style="color: #a0d2eb; font-size: 12px;">
                                    {update.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
                                </p>
                                <p>{update.summary or update.full_content[:300]}...</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Citations
                            if update.citations:
                                st.markdown("**Citations:**")
                                for citation in update.citations:
                                    if isinstance(citation, dict):
                                        url = citation.get('url', '')
                                        title = citation.get('title', url)
                                    else:
                                        url = citation
                                        title = url
                                    
                                    st.markdown(f'<span class="citation">🔗 <a href="{url}" target="_blank">{title[:50]}</a></span>', unsafe_allow_html=True)
                            
                            # Full content expander
                            if update.full_content:
                                with st.expander("📄 Full Content"):
                                    st.text_area("", update.full_content, height=200, key=f"content_{update.id}")
                    
                    # Generate Report Button
                    if updates:
                        st.markdown("---")
                        
                        # Use session state to persist report
                        report_key = f"briefing_report_{scout.id}"
                        
                        if st.button("📝 Generate Intelligence Briefing", key=f"gen_btn_{scout.id}", type="primary", use_container_width=True):
                            with st.spinner("Synthesizing updates into briefing..."):
                                try:
                                    from app.agents import UpdateSynthesizer
                                    
                                    async def synthesize():
                                        synth = UpdateSynthesizer()
                                        return await synth.synthesize_updates(scout.original_query, updates)
                                    
                                    report = asyncio.run(synthesize())
                                    st.session_state[report_key] = report
                                    
                                except Exception as e:
                                    st.error(f"Failed to generate briefing: {e}")
                        
                        # Display report if it exists in session state
                        if report_key in st.session_state:
                            report = st.session_state[report_key]
                            st.markdown("### 📝 Intelligence Briefing")
                            st.markdown(f'<div class="panel">{report}</div>', unsafe_allow_html=True)
                            
                            st.download_button(
                                "📥 Download Briefing",
                                report,
                                file_name=f"briefing_{scout.id[:8]}.md",
                                key=f"dl_{scout.id}"
                            )
                            
                            if st.button("❌ Close Report", key=f"close_{scout.id}"):
                                del st.session_state[report_key]
                                st.rerun()


# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: white; padding: 20px;">
    <p>📡 Yutori Monitoring | Powered by Yutori Scouting API</p>
</div>
""", unsafe_allow_html=True)

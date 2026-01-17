# --- Imports ---
import streamlit as st
import uuid
import json
import os
import time
import threading
import asyncio
import pandas as pd
from datetime import datetime
import sys

# Ensure app is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ops import RunLogger
from app.graph import app_graph
from app.images import ImageSuggestionAgent, ImageGenerator
from app.images.models import ImageStatus

# --- Configuration & State ---
RUNS_DIR = os.path.join(os.path.dirname(__file__), "..", "cache", "runs")
os.makedirs(RUNS_DIR, exist_ok=True)

st.set_page_config(
    page_title="TinyScout Research",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Minimalist Dark Theme ---
st.markdown("""
<style>
    /* Minimalist Dark Theme */
    .stApp { background-color: #0e1117; color: #fafafa; }
    .block-container { padding-top: 2rem; }
    .main-header { text-align: center; margin-bottom: 2rem; border-bottom: 1px solid #262730; padding-bottom: 1rem; }
    .main-header h1 { font-weight: 700; margin-bottom: 0.5rem; }
    .input-container { background-color: #262730; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1.5rem; }
    .panel { background-color: #1c1c21; border: 1px solid #262730; border-radius: 0.5rem; padding: 1.5rem; margin-bottom: 1rem; }
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
    .badge-running { background: #1e3a8a; color: #93c5fd; }
    .badge-completed { background: #064e3b; color: #6ee7b7; }
    .badge-failed { background: #7f1d1d; color: #fca5a5; }
    pre { background-color: #1c1c21; border: 1px solid #333; padding: 10px; border-radius: 4px; white-space: pre-wrap; }
    .stButton > button { width: 100%; }
    
    /* Image Grid */
    .img-grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    .img-card {
        background-color: #1c1c21;
        border: 1px solid #262730;
        border-radius: 0.5rem;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- A) Make run state explicit ---
if "active_run_id" not in st.session_state:
    st.session_state.active_run_id = None

# --- Helpers for File-Based State ---
def get_run_file(run_id):
    return os.path.join(RUNS_DIR, f"{run_id}.json")

def save_run_state(run_id, state_data):
    with open(get_run_file(run_id), 'w') as f:
        json.dump(state_data, f, indent=2, default=str)

def load_run_state(run_id):
    path = get_run_file(run_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return None

# --- C) Background Job (Worker) ---
def run_research_worker(run_id, query, model, retriever, generate_images):
    """
    Worker thread function. NEVER calls Streamlit directly.
    Writes strictly to JSON file.
    """
    # Initialize state
    state = {
        "id": run_id,
        "status": "running",
        "query": query,
        "config": {"model": model, "retriever": retriever, "generate_images": generate_images},
        "progress": 0,
        "logs": ["Research process started..."],
        "result": None,
        "images": [],
        "error": None,
        "timestamp": datetime.now().isoformat()
    }
    save_run_state(run_id, state)

    # Async wrapper
    async def _async_work():
        try:
            # Need to initialize logger if needed, but for simplicity we log to JSON state
            inputs = {"query": query}
            final_report = ""
            
            # Run the graph
            async for event in app_graph.astream(inputs, config={"recursion_limit": 50}):
                 for key, value in event.items():
                    # Check current state (reload to avoid overwriting)
                    current_state = load_run_state(run_id) or state
                    
                    # 1. Update Progress based on Node
                    if key == "planner":
                        tasks = value.get("plan", [])
                        count = len(tasks) if isinstance(tasks, list) else 0
                        current_state['logs'].append(f"📋 Planner: Generated {count} tasks")
                        current_state['progress'] = 20
                        
                    elif key == "web_research":
                         findings = value.get("findings", [])
                         count = len(findings) if isinstance(findings, list) else 0
                         current_state['logs'].append(f"🌍 Web Agent: Found {count} items")
                         current_state['progress'] = 60
                         
                    elif key == "synthesizer":
                        current_state['logs'].append("✍️ Synthesizer: writing report...")
                        current_state['progress'] = 80

                    # 2. Check for Final Report (can come from synthesizer OR web_research early exit)
                    if "final_report" in value and value["final_report"]:
                        report_obj = value["final_report"]
                        # Handle Pydantic model
                        if hasattr(report_obj, 'formatted_report'):
                            txt_report = report_obj.formatted_report
                        else:
                            txt_report = str(report_obj)
                            
                        current_state['result'] = txt_report
                        final_report = txt_report # Local var for image gen check
                        current_state['logs'].append("✅ Report captured")

                    save_run_state(run_id, current_state)
            
            # --- Image Generation Logic ---
            if generate_images and final_report:
                img_state = load_run_state(run_id)
                img_state['logs'].append("✨ Analyzer: Checking for visual opportunities...")
                save_run_state(run_id, img_state)
                
                try:
                    # Suggestion
                    suggestion_agent = ImageSuggestionAgent()
                    suggestion = await suggestion_agent.suggest_images(
                        query=query,
                        report_outline="", 
                        report_summary=final_report[:2000] # Use part of report as summary
                    )
                    
                    if suggestion.should_generate and suggestion.images:
                        img_state['logs'].append(f"🎨 Generator: Creating {len(suggestion.images)} visuals...")
                        save_run_state(run_id, img_state)
                        
                        generator = ImageGenerator()
                        artifacts = await generator.generate_images(suggestion.images)
                        
                        # Save image data to state
                        img_data = []
                        for art in artifacts:
                            if art.status == ImageStatus.COMPLETED:
                                img_data.append({
                                    "title": art.title,
                                    "url": art.image_url,
                                    "path": art.local_path,
                                    "prompt": art.prompt
                                })
                        
                        img_state = load_run_state(run_id)
                        img_state['images'] = img_data
                        img_state['logs'].append(f"✅ Generated {len(img_data)} images")
                    else:
                        img_state = load_run_state(run_id)
                        img_state['logs'].append("ℹ️ No suitable visuals found")
                
                except Exception as img_err:
                    err_state = load_run_state(run_id)
                    err_state['logs'].append(f"⚠️ Image Gen Failed: {str(img_err)}")
                    save_run_state(run_id, err_state)
                
                save_run_state(run_id, img_state)

            # Finalize
            final_state = load_run_state(run_id)
            final_state['status'] = 'completed'
            final_state['progress'] = 100
            final_state['logs'].append("✅ Research execution complete")
            save_run_state(run_id, final_state)
            
        except Exception as e:
            err_state = load_run_state(run_id)
            err_state['status'] = 'failed'
            err_state['error'] = str(e)
            err_state['logs'].append(f"❌ Error: {str(e)}")
            save_run_state(run_id, err_state)

    # Run asyncio loop in this thread
    asyncio.run(_async_work())


# --- UI Layout ---

# Header
st.markdown('<div class="main-header"><h1>TinyScout Research</h1></div>', unsafe_allow_html=True)

# Input
with st.container():
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Research Goal", placeholder="e.g. Latest trends in solid state batteries")
    
    # Settings
    with st.expander("⚙️ Settings"):
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            model = st.selectbox("Model", ["claude-sonnet-4-5", "claude-3-opus"], key="model_sel")
        with col_s2:
            retriever = st.selectbox("Retriever", ["tinyfish", "http"], key="ret_sel")
        with col_s3:
            gen_visuals = st.checkbox("✨ Generate Visuals", value=True)

    # B) On Start Research
    with col2:
        st.write("") # Spacer
        st.write("")
        if st.button("🚀 Start", type="primary"):
            if not query:
                st.error("Please enter a query")
            else:
                # 1. Generate ID
                run_id = str(uuid.uuid4())
                
                # 2. Update Session State
                st.session_state.active_run_id = run_id
                
                # 3. Start Background Job
                t = threading.Thread(
                    target=run_research_worker,
                    args=(run_id, query, model, retriever, gen_visuals)
                )
                t.start()
                
                # 4. Rerun immediately to enter Poll mode
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# --- D) Poll + Render ---
run_id = st.session_state.active_run_id

if run_id:
    # 1. Load run state from file (Single source of truth)
    run_state = load_run_state(run_id)
    
    if not run_state:
        st.info("Initializing run...")
        time.sleep(0.5)
        st.rerun()
    else:
        status = run_state.get('status', 'unknown')
        
        # Display Status Panel
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        cols = st.columns([2, 4, 1])
        with cols[0]:
            st.caption("Run ID")
            st.code(run_id[:8])
        with cols[1]:
            st.caption("Status")
            badge_class = f"badge-{status}"
            st.markdown(f'<span class="badge {badge_class}">{status.upper()}</span>', unsafe_allow_html=True)
            if status == "running":
                st.progress(run_state.get('progress', 0) / 100)
        with cols[2]:
             if st.button("🔄 New"):
                st.session_state.active_run_id = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # -- Auto-refresh logic (Polling) --
        if status == "running":
            time.sleep(1.5)
            st.rerun()
        
        # -- Render Report if Completed --
        if status == "completed":
            result = run_state.get('result')
            images = run_state.get('images', [])
            
            # 1. Report
            if result:
                st.markdown("### 📄 Research Report")
                st.markdown('<div class="report-container">', unsafe_allow_html=True)
                st.markdown(result)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 2. Images (Grid)
            if images:
                st.markdown("### 🎨 Generated Visuals")
                cols = st.columns(3)
                for idx, img in enumerate(images):
                    col = cols[idx % 3]
                    with col:
                        # Prioritize URL if available, else local path
                        img_src = img.get('url') or img.get('path')
                        if img_src:
                            st.image(img_src, caption=img.get('title', 'Generated Image'), use_container_width=True)
                        with st.expander("Details"):
                            st.caption(f"Prompt: {img.get('prompt')}")
            
            # Downloads
            if result:
                 st.download_button(
                    "📥 Download MD",
                    result,
                    file_name=f"report_{run_id[:8]}.md"
                )
        
        # -- Render Error if Failed --
        if status == "failed":
            st.error(f"Run Failed: {run_state.get('error')}")

        # --- Debug Panels ---
        st.markdown("---")
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            with st.expander("🔍 Debug: Raw Result JSON", expanded=False):
                st.json(run_state)
        
        with col_d2:
            with st.expander("📜 Logs", expanded=True):
                logs = run_state.get('logs', [])
                if logs:
                     # Show last 10 logs
                    st.code("\n".join(logs[-10:]), language="text")
                else:
                    st.caption("No logs yet...")

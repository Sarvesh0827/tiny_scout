import streamlit as st
import asyncio
import sys
import os

# Ensure app is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.graph import app_graph
from app.models import ResearchTask

st.set_page_config(page_title="TinyScout", page_icon="🕵️", layout="wide")

st.title("🕵️ TinyScout: Autonomous Research Agent")
st.markdown("Enter a research goal, and watch the agent plan, browse, and synthesize.")

query = st.text_input("Research Goal:", "Research the top 5 AI voice moderation competitors.")

if st.button("Start Research"):
    st.info("Initializing Agent Team...")
    
    # Containers for live updates
    status_container = st.container()
    with status_container:
        st.subheader("Agent Activity Log")
        log_area = st.empty()
    
    findings_container = st.container()
    with findings_container:
        st.subheader("Research Findings")
        findings_area = st.empty()

    report_container = st.container()
    with report_container:
        st.subheader("Final Report")
        report_area = st.empty()
    
    trace_container = st.container()
    with trace_container:
        st.subheader("🔍 Browser Trace")
        trace_area = st.empty()

    async def run_research():
        initial_state = {
            "query": query,
            "plan": [],
            "findings": [],
            "final_report": None,
            "messages": []
        }
        
        logs = []
        all_findings = []
        
        try:
            async for output in app_graph.astream(initial_state):
                for key, value in output.items():
                    # Update Logs
                    if "messages" in value:
                        for m in value["messages"]:
                            logs.append(f"**[{key.upper()}]**: {m}")
                            log_area.markdown("\n".join(logs))
                    
                    # Update Findings
                    if "findings" in value:
                        new_findings = value["findings"]
                        for f in new_findings:
                            all_findings.append(f)
                            
                        # Refresh findings view
                        with findings_area.container():
                            for f in all_findings:
                                with st.expander(f"Source: {f.source_url}", expanded=False):
                                    st.write(f"**Relevance:** {f.relevance_score}")
                                    st.write(f.content[:500] + "...")
                                    if f.extracted_data:
                                        st.json(f.extracted_data)
                        
                        # Update Browser Trace (with None guards)
                        if all_findings:
                            last_finding = all_findings[-1]
                            if hasattr(last_finding, 'extracted_data') and last_finding.extracted_data:
                                trace_data = last_finding.extracted_data
                                if trace_data and 'retrieval_methods' in trace_data and 'urls' in trace_data:
                                    with trace_area.expander("🔍 Retrieval Details", expanded=True):
                                        urls = trace_data.get('urls', []) or []
                                        methods = trace_data.get('retrieval_methods', []) or []
                                        for i, (url, method) in enumerate(zip(urls, methods)):
                                            st.write(f"**{i+1}. {url}**")
                                            st.caption(f"Method: `{method}`")

                    # Update Report
                    if "final_report" in value and value["final_report"]:
                        report_area.markdown(value["final_report"].formatted_report)
                        
        except Exception as e:
            st.error(f"An error occurred: {e}")

    # Run the async function
    asyncio.run(run_research())

st.sidebar.markdown("### Availability")
import os
from dotenv import load_dotenv
load_dotenv()
active_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
st.sidebar.success(f"🟢 Claude Active")
st.sidebar.caption(f"Model: {active_model}")

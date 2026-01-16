from langgraph.graph import StateGraph, END
from app.state import AgentState
from app.agents.planner import PlannerAgent
from app.agents.web_agent import WebAgent
from app.agents.analyzer import AnalyzerAgent
from app.agents.synthesizer import SynthesizerAgent
from app.models import ResearchTask, ResearchFinding

# Initialize Agents
planner = PlannerAgent(model_name="mistral")
web_agent = WebAgent()
analyzer = AnalyzerAgent(model_name="mistral")
synthesizer = SynthesizerAgent(model_name="mistral")

async def plan_node(state: AgentState):
    result = await planner.plan(state)
    return result

async def web_execution_node(state: AgentState):
    # Retrieve the latest plan
    tasks = state['plan']
    findings = []
    messages = []
    
    # Simple sequential execution for simulation
    # In full version, we'd use 'map' parallel execution
    for task in tasks:
        if task.status == "pending":
            msg = f"Running task: {task.description}"
            messages.append(msg)
            print(msg)
            
            finding = await web_agent.execute_task(task)
            
            # 3. Analyze immediately
            analysis = await analyzer.analyze(finding.content, task.description)
            finding.extracted_data = finding.extracted_data or {}
            finding.extracted_data["analysis"] = analysis
            
            findings.append(finding)
            task.status = "completed"
    
    # Priority 2: Grounding Gate
    total_chars = sum([len(f.content) for f in findings])
    valid_sources = sum([1 for f in findings if f.source_url != "N/A"])
    
    # Priority 2: Grounding Gate
    total_chars = sum([len(f.content) for f in findings])
    valid_sources = sum([1 for f in findings if f.source_url != "N/A"])
    
    # If using seeded URLs or real search, we should have content.
    # If 0 sources OR < 1000 chars total text -> ABORT SYNTHESIS.
    if valid_sources == 0 or total_chars < 1000:
        msg = f"INSUFFICIENT EVIDENCE: Found {valid_sources} sources, {total_chars} chars. Stopping synthesis."
        messages.append(msg)
        print(msg)
        
        from app.models import FinalReport
        # Return a special "Error Report" directly, bypassing synthesizer node logic effectively
        # (Though we can just set final_report here and Graph will end)
        return {
            "findings": findings, 
            "plan": tasks, 
            "messages": messages,
            "final_report": FinalReport(
                summary="Research Failed: Insufficient Evidence",
                findings=[],
                sources=[],
                formatted_report=f"""
# Insufficient Evidence

The research agent could not find enough verifiable information to answer your query.

**Diagnostics:**
- **Queries Tried:** {[t.description for t in tasks]}
- **Sources Found:** {valid_sources}
- **Total Text Extracted:** {total_chars} characters

**Suggestion:**
Please try:
1. Refining your research goal.
2. Checking your internet connection (if local).
3. Providing specific URLs to analyze.
"""
            )
        }

    return {"findings": findings, "plan": tasks, "messages": messages}

async def synthesize_node(state: AgentState):
    # If we already have a final report (from error condition above), skip synthesis
    if state.get("final_report"):
        return {}
        
    result = await synthesizer.synthesize(state)
    return result

# Define the Graph
workflow = StateGraph(AgentState)

workflow.add_node("planner", plan_node)
workflow.add_node("web_research", web_execution_node)
workflow.add_node("synthesizer", synthesize_node)

workflow.set_entry_point("planner")

workflow.add_edge("planner", "web_research")
workflow.add_edge("web_research", "synthesizer")
workflow.add_edge("synthesizer", END)

# Compile
app_graph = workflow.compile()

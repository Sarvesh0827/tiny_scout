from typing import List, TypedDict, Annotated
import operator
from app.models import ResearchTask, FinalReport, ResearchFinding

class AgentState(TypedDict):
    """
    The state of the research agent graph.
    """
    query: str
    plan: List[ResearchTask]
    findings: Annotated[List[ResearchFinding], operator.add]  # Append-only list of findings
    final_report: FinalReport | None
    messages: List[str] # Log of agent actions/reasoning

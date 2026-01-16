from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ResearchRequest(BaseModel):
    query: str = Field(..., description="The main research question or topic.")
    max_depth: int = Field(default=2, description="Maximum depth of sub-questions.")

class ResearchFinding(BaseModel):
    source_url: str
    content: str
    relevance_score: float = 0.0
    extracted_data: Optional[Dict[str, Any]] = None

class ResearchTask(BaseModel):
    id: str
    description: str
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[ResearchFinding] = None

class ResearchPlan(BaseModel):
    main_goal: str
    tasks: List[ResearchTask] = []

class FinalReport(BaseModel):
    summary: str
    findings: List[ResearchFinding]
    sources: List[str]
    formatted_report: str

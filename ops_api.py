"""
FastAPI backend for Ops Console (Retool integration).
Read-only endpoints for observability.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ops.models import Run, RunEvent, Document, get_session

app = FastAPI(title="TinyScout Ops Console API")

# CORS for Retool
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API responses
class RunResponse(BaseModel):
    id: str
    created_at: datetime
    research_goal: str
    status: str
    planner_model: Optional[str]
    analyzer_model: Optional[str]
    synthesizer_model: Optional[str]
    retriever_backend: Optional[str]
    topic: Optional[str]
    final_report: Optional[str]
    error_message: Optional[str]
    doc_count: int = 0
    selected_count: int = 0
    
    class Config:
        from_attributes = True

class EventResponse(BaseModel):
    id: str
    run_id: str
    ts: datetime
    stage: str
    level: str
    message: str
    payload: Optional[dict]
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    run_id: str
    task: Optional[str]
    url: str
    retrieval_method: Optional[str]
    http_status: Optional[int]
    title: Optional[str]
    content_len: Optional[int]
    relevance_score: Optional[float]
    tier: Optional[str]
    selected: bool
    snippet: Optional[str]
    
    class Config:
        from_attributes = True

@app.get("/")
def root():
    """API root."""
    return {
        "service": "TinyScout Ops Console API",
        "version": "1.0.0",
        "endpoints": [
            "/api/runs",
            "/api/runs/{run_id}",
            "/api/runs/{run_id}/events",
            "/api/runs/{run_id}/documents"
        ]
    }

@app.get("/api/runs", response_model=List[RunResponse])
def get_runs(limit: int = 50, status: Optional[str] = None):
    """Get list of research runs."""
    session = get_session()
    
    query = session.query(Run).order_by(Run.created_at.desc())
    
    if status:
        query = query.filter(Run.status == status)
    
    runs = query.limit(limit).all()
    
    # Add counts
    result = []
    for run in runs:
        doc_count = session.query(Document).filter(Document.run_id == run.id).count()
        selected_count = session.query(Document).filter(
            Document.run_id == run.id,
            Document.selected == True
        ).count()
        
        run_dict = {
            "id": run.id,
            "created_at": run.created_at,
            "research_goal": run.research_goal,
            "status": run.status,
            "planner_model": run.planner_model,
            "analyzer_model": run.analyzer_model,
            "synthesizer_model": run.synthesizer_model,
            "retriever_backend": run.retriever_backend,
            "topic": run.topic,
            "final_report": run.final_report,
            "error_message": run.error_message,
            "doc_count": doc_count,
            "selected_count": selected_count
        }
        result.append(RunResponse(**run_dict))
    
    session.close()
    return result

@app.get("/api/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: str):
    """Get specific run details."""
    session = get_session()
    
    run = session.query(Run).filter(Run.id == run_id).first()
    
    if not run:
        session.close()
        raise HTTPException(status_code=404, detail="Run not found")
    
    doc_count = session.query(Document).filter(Document.run_id == run.id).count()
    selected_count = session.query(Document).filter(
        Document.run_id == run.id,
        Document.selected == True
    ).count()
    
    run_dict = {
        "id": run.id,
        "created_at": run.created_at,
        "research_goal": run.research_goal,
        "status": run.status,
        "planner_model": run.planner_model,
        "analyzer_model": run.analyzer_model,
        "synthesizer_model": run.synthesizer_model,
        "retriever_backend": run.retriever_backend,
        "topic": run.topic,
        "final_report": run.final_report,
        "error_message": run.error_message,
        "doc_count": doc_count,
        "selected_count": selected_count
    }
    
    session.close()
    return RunResponse(**run_dict)

@app.get("/api/runs/{run_id}/events", response_model=List[EventResponse])
def get_run_events(run_id: str, stage: Optional[str] = None, level: Optional[str] = None):
    """Get events for a specific run."""
    session = get_session()
    
    query = session.query(RunEvent).filter(RunEvent.run_id == run_id).order_by(RunEvent.ts)
    
    if stage:
        query = query.filter(RunEvent.stage == stage)
    if level:
        query = query.filter(RunEvent.level == level)
    
    events = query.all()
    session.close()
    
    return [EventResponse.from_orm(e) for e in events]

@app.get("/api/runs/{run_id}/documents", response_model=List[DocumentResponse])
def get_run_documents(run_id: str, selected_only: bool = False):
    """Get documents for a specific run."""
    session = get_session()
    
    query = session.query(Document).filter(Document.run_id == run_id)
    
    if selected_only:
        query = query.filter(Document.selected == True)
    
    documents = query.all()
    session.close()
    
    return [DocumentResponse.from_orm(d) for d in documents]

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

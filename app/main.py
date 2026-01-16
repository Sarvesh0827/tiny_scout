from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from app.models import ResearchRequest

app = FastAPI(title="TinyScout API", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "TinyScout Research Agent API"}

@app.post("/research")
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    # TODO: Initialize LangGraph workflow and start execution
    return {"message": "Research started", "query": request.query}

"""
RunLogger: Dual-output logging (console + database).
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any
from .models import Run, RunEvent, Document, get_session, init_db

class RunLogger:
    """
    Structured logger that writes to both console and database.
    Carries run_id through the entire pipeline.
    """
    
    def __init__(self, run_id: str, research_goal: str, config: Dict[str, str]):
        self.run_id = run_id
        self.research_goal = research_goal
        self.config = config
        self.session = get_session()
        
        # Create run record
        self.run = Run(
            id=run_id,
            research_goal=research_goal,
            planner_model=config.get('planner_model'),
            analyzer_model=config.get('analyzer_model'),
            synthesizer_model=config.get('synthesizer_model'),
            retriever_backend=config.get('retriever_backend'),
            status='running'
        )
        self.session.add(self.run)
        self.session.commit()
        
        print(f"[RUN:{run_id[:8]}] Started: {research_goal}")
    
    def log(
        self,
        stage: str,
        message: str,
        level: str = 'info',
        payload: Optional[Dict[str, Any]] = None
    ):
        """Log an event to both console and database."""
        # Console output
        level_emoji = {
            'info': 'ℹ️',
            'warn': '⚠️',
            'error': '❌',
            'debug': '🔍'
        }
        emoji = level_emoji.get(level, 'ℹ️')
        print(f"[{stage.upper()}] {emoji} {message}")
        
        # Database output
        event = RunEvent(
            run_id=self.run_id,
            stage=stage,
            level=level,
            message=message,
            payload=payload
        )
        self.session.add(event)
        self.session.commit()
    
    def log_document(
        self,
        task: str,
        url: str,
        retrieval_method: str,
        content_len: int = 0,
        **kwargs
    ):
        """Log a fetched document."""
        doc = Document(
            run_id=self.run_id,
            task=task,
            url=url,
            retrieval_method=retrieval_method,
            content_len=content_len,
            http_status=kwargs.get('http_status'),
            title=kwargs.get('title'),
            relevance_score=kwargs.get('relevance_score'),
            tier=kwargs.get('tier', 'unknown'),
            selected=kwargs.get('selected', False),
            snippet=kwargs.get('snippet'),
            raw_text_path=kwargs.get('raw_text_path')
        )
        self.session.add(doc)
        self.session.commit()
        
        print(f"[DOCUMENT] {url} | {retrieval_method} | {content_len} chars")
    
    def update_run(self, **kwargs):
        """Update run metadata."""
        for key, value in kwargs.items():
            if hasattr(self.run, key):
                setattr(self.run, key, value)
        self.session.commit()
    
    def set_status(self, status: str, error_message: Optional[str] = None):
        """Set run status."""
        self.run.status = status
        if error_message:
            self.run.error_message = error_message
        self.session.commit()
        
        status_emoji = {
            'success': '✅',
            'failed': '❌',
            'insufficient_evidence': '⚠️'
        }
        emoji = status_emoji.get(status, '🔄')
        print(f"[RUN:{self.run_id[:8]}] {emoji} Status: {status}")
    
    def set_topic(self, topic: str):
        """Set classified topic."""
        self.run.topic = topic
        self.session.commit()
        print(f"[RUN:{self.run_id[:8]}] Topic: {topic}")
    
    def set_final_report(self, report: str):
        """Set final report."""
        self.run.final_report = report
        self.session.commit()
    
    def close(self):
        """Close database session."""
        self.session.close()

# Initialize database on import
init_db()

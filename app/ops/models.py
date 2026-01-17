"""
Database models for ops logging and observability.
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()

class Run(Base):
    """Research run metadata."""
    __tablename__ = 'runs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    research_goal = Column(Text, nullable=False)
    status = Column(String, default='running')  # running/success/failed/insufficient_evidence
    planner_model = Column(String)
    analyzer_model = Column(String)
    synthesizer_model = Column(String)
    retriever_backend = Column(String)  # tinyfish/http
    topic = Column(String)
    final_report = Column(Text)
    error_message = Column(Text)
    
    # Relationships
    events = relationship("RunEvent", back_populates="run", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="run", cascade="all, delete-orphan")

class RunEvent(Base):
    """Structured event log for each run."""
    __tablename__ = 'run_events'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey('runs.id'), nullable=False)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)
    stage = Column(String, nullable=False)  # planner/retriever/web_agent/analyzer/synthesizer
    level = Column(String, default='info')  # info/warn/error/debug
    message = Column(Text, nullable=False)
    payload = Column(JSON)  # Structured data
    
    # Relationship
    run = relationship("Run", back_populates="events")

class Document(Base):
    """Document fetched and processed during research."""
    __tablename__ = 'documents'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey('runs.id'), nullable=False)
    task = Column(Text)
    url = Column(Text, nullable=False)
    retrieval_method = Column(String)  # tinyfish/http/cache
    http_status = Column(Integer)
    title = Column(Text)
    content_len = Column(Integer)
    relevance_score = Column(Float)
    tier = Column(String)  # A/B/C/unknown
    selected = Column(Boolean, default=False)
    snippet = Column(Text)  # First 500 chars
    raw_text_path = Column(String)  # Optional file path for full text
    
    # Relationship
    run = relationship("Run", back_populates="documents")

# Database setup
import os

# Get absolute path to cache directory in project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
DB_PATH = os.path.join(CACHE_DIR, "ops_console.db")

def get_engine(db_path: str = None):
    """Create SQLite engine."""
    if db_path is None:
        db_path = DB_PATH
    return create_engine(f"sqlite:///{db_path}", echo=False)

def init_db(db_path: str = None):
    """Initialize database schema."""
    if db_path is None:
        db_path = DB_PATH
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine=None):
    """Get database session."""
    if engine is None:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

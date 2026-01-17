"""
Persistence layer for Yutori Scout monitoring.
Stores scout metadata and updates in SQLite.
"""
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Scout(Base):
    """Scout task metadata."""
    __tablename__ = 'scouts'
    
    id = Column(String, primary_key=True)  # Yutori scout_id
    query = Column(Text, nullable=False)
    original_query = Column(Text)  # User's original query
    output_interval = Column(Integer, nullable=False)  # Seconds
    user_timezone = Column(String, default='America/Los_Angeles')
    webhook_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    next_run_timestamp = Column(DateTime)
    last_cursor = Column(String)  # For pagination
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSON)  # Store full Yutori response

class ScoutUpdate(Base):
    """Individual update from a scout."""
    __tablename__ = 'scout_updates'
    
    id = Column(String, primary_key=True)  # Yutori update_id or generated
    scout_id = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    headline = Column(Text)
    summary = Column(Text)
    citations = Column(JSON)  # List of URLs/sources
    full_content = Column(Text)
    metadata_json = Column(JSON)  # Store full update data
    created_at = Column(DateTime, default=datetime.utcnow)

# Database setup
def get_engine(db_path: str = "cache/scouts.db"):
    """Create SQLite engine."""
    return create_engine(f"sqlite:///{db_path}", echo=False)

def init_db(db_path: str = "cache/scouts.db"):
    """Initialize database schema."""
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

# Initialize on import
init_db()

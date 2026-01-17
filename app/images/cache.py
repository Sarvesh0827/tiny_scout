"""
Image generation cache using SQLite.
"""
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List
from .models import ImageArtifact, ImageStatus
import os

CACHE_DB_PATH = "cache/image_cache.db"

class ImageCache:
    """SQLite-based cache for generated images."""
    
    def __init__(self, db_path: str = CACHE_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_cache (
                cache_key TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                aspect_ratio TEXT,
                style TEXT,
                task_id TEXT,
                image_url TEXT,
                local_path TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TIMESTAMP NOT NULL,
                accessed_at TIMESTAMP NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def generate_cache_key(title: str, prompt: str, aspect_ratio: str, style: Optional[str] = None) -> str:
        """Generate cache key from image parameters."""
        key_data = f"{title}|{prompt}|{aspect_ratio}|{style or ''}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, cache_key: str) -> Optional[ImageArtifact]:
        """Retrieve cached image."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, prompt, aspect_ratio, style, task_id, image_url, 
                   local_path, status, error_message, created_at
            FROM image_cache
            WHERE cache_key = ?
        """, (cache_key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Update access time
        self._update_access_time(cache_key)
        
        return ImageArtifact(
            title=row[0],
            prompt=row[1],
            aspect_ratio=row[2],
            style=row[3],
            task_id=row[4],
            image_url=row[5],
            local_path=row[6],
            status=ImageStatus(row[7]),
            error_message=row[8],
            created_at=datetime.fromisoformat(row[9]) if row[9] else None
        )
    
    def set(self, cache_key: str, artifact: ImageArtifact):
        """Store image in cache."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO image_cache 
            (cache_key, title, prompt, aspect_ratio, style, task_id, image_url, 
             local_path, status, error_message, created_at, accessed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cache_key,
            artifact.title,
            artifact.prompt,
            artifact.aspect_ratio,
            artifact.style,
            artifact.task_id,
            artifact.image_url,
            artifact.local_path,
            artifact.status.value,
            artifact.error_message,
            artifact.created_at.isoformat() if artifact.created_at else datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _update_access_time(self, cache_key: str):
        """Update last access time."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE image_cache
            SET accessed_at = ?
            WHERE cache_key = ?
        """, (datetime.now().isoformat(), cache_key))
        
        conn.commit()
        conn.close()
    
    def cleanup_old_entries(self, days: int = 30):
        """Remove cache entries older than N days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            DELETE FROM image_cache
            WHERE accessed_at < ?
        """, (cutoff,))
        
        conn.commit()
        conn.close()

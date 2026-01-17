"""
Scout Manager - Business logic for Yutori monitoring.
"""
from .yutori_client import YutoriClient, enhance_monitoring_query
from .models import Scout, ScoutUpdate, get_session
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

class ScoutManager:
    """Manages scout lifecycle and updates."""
    
    def __init__(self):
        self.client = YutoriClient()
        self.session = get_session()
    
    async def create_scout(
        self,
        query: str,
        interval_minutes: int,
        enhance_query: bool = True,
        webhook_url: Optional[str] = None
    ) -> Scout:
        """
        Create and persist a new scout.
        
        Args:
            query: User's monitoring query
            interval_minutes: Update frequency in minutes
            enhance_query: Whether to enhance query for monitoring
            webhook_url: Optional webhook URL
            
        Returns:
            Scout database record
        """
        # Enhance query if requested
        monitoring_query = enhance_monitoring_query(query) if enhance_query else query
        interval_seconds = interval_minutes * 60
        
        # Create scout via Yutori API
        response = await self.client.create_scout(
            query=monitoring_query,
            interval_seconds=interval_seconds,
            webhook_url=webhook_url
        )
        
        # Parse response
        scout_id = response.get("id")
        next_run = response.get("next_run_timestamp")
        
        # Convert timestamp if string
        if isinstance(next_run, str):
            try:
                next_run = datetime.fromisoformat(next_run.replace('Z', '+00:00'))
            except:
                next_run = None
        
        # Create database record
        scout = Scout(
            id=scout_id,
            query=monitoring_query,
            original_query=query,
            output_interval=interval_seconds,
            next_run_timestamp=next_run,
            webhook_url=webhook_url,
            metadata_json=response
        )
        
        self.session.add(scout)
        self.session.commit()
        
        print(f"[SCOUT_MGR] Scout created and persisted: {scout_id[:8]}...")
        return scout
    
    async def fetch_updates(self, scout_id: str) -> List[ScoutUpdate]:
        """
        Fetch new updates for a scout.
        Uses cursor to avoid reprocessing.
        
        Returns:
            List of new ScoutUpdate records
        """
        # Get scout from DB
        scout = self.session.query(Scout).filter(Scout.id == scout_id).first()
        if not scout:
            raise ValueError(f"Scout {scout_id} not found")
        
        # Fetch updates from Yutori
        response = await self.client.get_updates(
            scout_id=scout_id,
            cursor=scout.last_cursor
        )
        
        updates_data = response.get("items", [])
        next_cursor = response.get("next_cursor")
        
        # Process and store updates
        new_updates = []
        for update_data in updates_data:
            # Extract fields (adjust based on actual Yutori response format)
            update_id = update_data.get("id", str(uuid.uuid4()))
            timestamp_str = update_data.get("timestamp") or update_data.get("created_at")
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.utcnow()
            
            # Extract content
            headline = update_data.get("headline") or update_data.get("title")
            summary = update_data.get("summary") or update_data.get("content", "")[:500]
            citations = update_data.get("citations") or update_data.get("sources", [])
            full_content = update_data.get("content") or update_data.get("full_text", "")
            
            # Check if already exists
            existing = self.session.query(ScoutUpdate).filter(
                ScoutUpdate.id == update_id
            ).first()
            
            if not existing:
                update = ScoutUpdate(
                    id=update_id,
                    scout_id=scout_id,
                    timestamp=timestamp,
                    headline=headline,
                    summary=summary,
                    citations=citations,
                    full_content=full_content,
                    metadata_json=update_data
                )
                
                self.session.add(update)
                new_updates.append(update)
        
        # Update cursor
        if next_cursor:
            scout.last_cursor = next_cursor
        
        self.session.commit()
        
        print(f"[SCOUT_MGR] Fetched {len(new_updates)} new updates for {scout_id[:8]}...")
        return new_updates
    
    def get_all_scouts(self, active_only: bool = True) -> List[Scout]:
        """Get all scouts from database."""
        query = self.session.query(Scout)
        if active_only:
            query = query.filter(Scout.is_active == True)
        return query.order_by(Scout.created_at.desc()).all()
    
    def get_scout_updates(self, scout_id: str, limit: int = 50) -> List[ScoutUpdate]:
        """Get updates for a specific scout."""
        return self.session.query(ScoutUpdate).filter(
            ScoutUpdate.scout_id == scout_id
        ).order_by(ScoutUpdate.timestamp.desc()).limit(limit).all()
    
    async def delete_scout(self, scout_id: str) -> bool:
        """Delete scout from Yutori and mark inactive in DB."""
        # Delete from Yutori
        success = await self.client.delete_scout(scout_id)
        
        # Mark inactive in DB
        scout = self.session.query(Scout).filter(Scout.id == scout_id).first()
        if scout:
            scout.is_active = False
            self.session.commit()
        
        return success
    
    def close(self):
        """Close database session."""
        self.session.close()

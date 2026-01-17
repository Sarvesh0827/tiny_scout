"""
Yutori Scouting API Client
Enables scheduled monitoring and periodic updates for research topics.
"""
import httpx
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class YutoriClient:
    """Client for Yutori Scouting API."""
    
    BASE_URL = "https://api.yutori.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("YUTORI_API_KEY")
        if not self.api_key:
            raise ValueError("YUTORI_API_KEY not found in environment")
        
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def create_scout(
        self,
        query: str,
        interval_seconds: int,
        webhook_url: Optional[str] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        user_timezone: str = "America/Los_Angeles"
    ) -> Dict[str, Any]:
        """
        Create a new scout task for scheduled monitoring.
        
        Args:
            query: Natural language monitoring query
            interval_seconds: Update frequency (minimum 1800 = 30 min)
            webhook_url: Optional webhook for push updates
            output_schema: Optional JSON schema for structured output
            user_timezone: Timezone for scheduling
            
        Returns:
            Scout metadata including scout_id and next_run_timestamp
        """
        if interval_seconds < 1800:
            raise ValueError("interval_seconds must be >= 1800 (30 minutes)")
        
        payload = {
            "query": query,
            "output_interval": interval_seconds,
            "user_timezone": user_timezone,
            "skip_email": True
        }
        
        if webhook_url:
            payload["webhook_url"] = webhook_url
        
        if output_schema:
            payload["task_spec"] = {
                "output_schema": {
                    "json_schema": output_schema
                }
            }
        
        print(f"[YUTORI] Creating scout: {query[:60]}...")
        print(f"[YUTORI] Interval: {interval_seconds}s ({interval_seconds // 60} min)")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/scouting/tasks",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                scout_id = data.get("id")
                next_run = data.get("next_run_timestamp")
                
                print(f"[YUTORI] ✅ Scout created: {scout_id}")
                print(f"[YUTORI] Next run: {next_run}")
                
                return data
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            print(f"[YUTORI] ❌ Error creating scout: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            print(f"[YUTORI] ❌ Error: {e}")
            raise
    
    async def get_updates(
        self,
        scout_id: str,
        cursor: Optional[str] = None,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get updates for a scout task.
        
        Args:
            scout_id: Scout task ID
            cursor: Pagination cursor (from previous response)
            page_size: Number of updates to fetch
            
        Returns:
            Updates data with items and next_cursor
        """
        params = {"page_size": page_size}
        if cursor:
            params["cursor"] = cursor
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/scouting/tasks/{scout_id}/updates",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                updates = data.get("items", [])
                next_cursor = data.get("next_cursor")
                
                print(f"[YUTORI] Fetched {len(updates)} updates for scout {scout_id[:8]}...")
                if next_cursor:
                    print(f"[YUTORI] Next cursor: {next_cursor[:20]}...")
                
                return {
                    "items": updates,
                    "next_cursor": next_cursor,
                    "has_more": bool(next_cursor)
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # No updates found is normal for new scouts
                print(f"[YUTORI] ℹ️ No updates found for scout {scout_id[:8]}...")
                return {"items": [], "next_cursor": None, "has_more": False}
                
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            print(f"[YUTORI] ❌ Error fetching updates: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            print(f"[YUTORI] ❌ Error: {e}")
            raise
    
    async def get_scout_status(self, scout_id: str) -> Dict[str, Any]:
        """Get scout task status and metadata."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/scouting/tasks/{scout_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"[YUTORI] ❌ Error getting scout status: {e}")
            raise
    
    async def delete_scout(self, scout_id: str) -> bool:
        """Delete/stop a scout task."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.delete(
                    f"{self.BASE_URL}/scouting/tasks/{scout_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                print(f"[YUTORI] ✅ Scout {scout_id[:8]}... deleted")
                return True
        except Exception as e:
            print(f"[YUTORI] ❌ Error deleting scout: {e}")
            return False


def enhance_monitoring_query(user_query: str) -> str:
    """
    Enhance user query for better monitoring results.
    Adds monitoring-specific instructions without restricting domains.
    """
    monitoring_aspects = [
        "latest news",
        "announcements",
        "updates",
        "policy changes",
        "pricing changes",
        "product releases",
        "acquisitions",
        "funding rounds",
        "regulatory actions",
        "partnerships"
    ]
    
    enhanced = f"""Monitor for: {user_query}

Focus on:
- {', '.join(monitoring_aspects)}
- Any significant changes or developments
- Official statements and press releases

Provide updates with clear citations and timestamps."""
    
    return enhanced

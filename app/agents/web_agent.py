import httpx
from duckduckgo_search import DDGS
import trafilatura
import asyncio
import logging
import hashlib
import os
from typing import List, Dict, Optional
from app.models import ResearchTask, ResearchFinding
from app.seeds import SEEDS_BY_CATEGORY, KEYWORDS

logger = logging.getLogger(__name__)

CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

class WebAgent:
    def __init__(self):
        # self.ddgs = DDGS() # Disabled for now to force Seed Mode as requested
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
    def _get_cache_path(self, url: str) -> str:
        """Simple disk cache path based on URL hash."""
        hash_digest = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(CACHE_DIR, f"{hash_digest}.txt")

    def _get_seeds_for_task(self, task_description: str) -> List[str]:
        """Selects the best seed URLs based on task keywords."""
        desc_lower = task_description.lower()
        if "player" in desc_lower or "competitor" in desc_lower or "company" in desc_lower:
            return SEEDS_BY_CATEGORY["key_players"]
        elif "trend" in desc_lower or "future" in desc_lower:
            return SEEDS_BY_CATEGORY["trends"]
        elif "need" in desc_lower or "challenge" in desc_lower or "limitation" in desc_lower or "gap" in desc_lower:
            return SEEDS_BY_CATEGORY["unmet_needs"]
        else:
            return SEEDS_BY_CATEGORY["default"]

    async def _search(self, query: str, max_results=5) -> List[str]:
        """Disabled DDG for now to force robust seeded URLs."""
        # For this iteration, we bypass DDG entirely to ensure we use our high-quality seeds.
        # In production, we would uncomment the DDG logic here.
        return []

    async def _fetch_and_extract(self, url: str) -> Optional[ResearchFinding]:
        """Step B & C: Robust Fetch with Caching & Simplified Extract."""
        
        # Check Cache First
        cache_path = self._get_cache_path(url)
        if os.path.exists(cache_path):
            print(f"DEBUG: Cache hit for {url}")
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read()
            return ResearchFinding(
                source_url=url,
                content=content,
                relevance_score=1.0,
                extracted_data={"cached": True}
            )

        print(f"DEBUG: Fetching {url}")
        html_content = ""
        
        # 1. Try httpx (Async)
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=True) as client: # Verify=True for security
                resp = await client.get(url, headers=self.headers)
                resp.raise_for_status()
                html_content = resp.text
        except Exception as e:
            print(f"DEBUG: Httpx failed for {url}: {e}. Retrying with Requests...")
            # 2. Key Fallback: Requests (Sync, but robust)
            try:
                import requests
                resp = requests.get(url, headers=self.headers, timeout=15, verify=True) # Verify=True
                resp.raise_for_status()
                html_content = resp.text
            except Exception as e2:
                 print(f"DEBUG: Requests failed for {url}: {e2}")
                 return None

        # Step C: Extract
        try:
            extracted = trafilatura.extract(html_content, include_comments=False, include_tables=True)
            
            # Loosen Thin Content Rule
            if extracted and len(extracted) > 200:
                print(f"DEBUG: Extracted {len(extracted)} chars from {url}")
                
                # Write to Cache
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(extracted)
                    
                return ResearchFinding(
                    source_url=url,
                    content=extracted,
                    relevance_score=1.0, 
                    extracted_data={"title": "Extracted Content"} 
                )
            else:
                print(f"DEBUG: Page skipped (Too thin): {url} (len={len(extracted) if extracted else 0})")
                return None
        except Exception as e:
             print(f"DEBUG: Extraction failed for {url}: {e}")
             return None

    def _score_relevance(self, content: str) -> int:
        """Scores content based on keyword hits."""
        score = 0
        content_lower = content.lower()
        for kw in KEYWORDS:
            score += content_lower.count(kw)
        return score

    async def execute_task(self, task: ResearchTask) -> ResearchFinding:
        """
        Executes search, fetch, extract loop with retry logic.
        """
        print(f"--- WEB AGENT: Processing '{task.description}' ---")
        
        # 1. Search (or get seeds)
        # Force SEEDS Mode for this task based on category logic
        urls = self._get_seeds_for_task(task.description)
        print(f"DEBUG: Selected {len(urls)} seeds for task: {task.description[:50]}...")
            
        # 3. Fetch & Extract (Parallel)
        tasks = [self._fetch_and_extract(u) for u in urls]
        results = await asyncio.gather(*tasks)
        
        # Filter valid results
        valid_findings = [r for r in results if r is not None]
        
        # 4. Relevance Scoring & Truncation
        scored_findings = []
        for f in valid_findings:
            score = self._score_relevance(f.content)
            f.relevance_score = float(score)
            scored_findings.append(f)
            
        # Sort by score descending
        scored_findings.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Top-K Selection (e.g. Top 3)
        top_findings = scored_findings[:3]
        
        if not top_findings:
             return ResearchFinding(source_url="N/A", content="No relevant text extracted.", relevance_score=0.0)

        combined_text = ""
        urls_list = []
        for f in top_findings:
            # Truncate long pages
            truncated_content = f.content[:3000] 
            combined_text += f"\n\n=== SOURCE: {f.source_url} (Score: {int(f.relevance_score)}) ===\n{truncated_content}" 
            urls_list.append(f.source_url)
            
        print(f"DEBUG: Final selection: {len(top_findings)} sources.")
        
        return ResearchFinding(
            source_url="Multiple Sources",
            content=combined_text, 
            relevance_score=1.0,
            extracted_data={"source_count": len(top_findings), "urls": urls_list}
        )

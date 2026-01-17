"""
HTTP-based retriever with robust search using ddgs.
"""
import httpx
import trafilatura
import hashlib
import os
import asyncio # Added imports
from typing import List, Optional
from ddgs import DDGS
from .base import BaseRetriever, Document, UrlCandidate
from app.seeds import classify_topic, get_seeds_for_topic
from app.config.search_config import INTENT_GUARDRAILS, QUERY_TEMPLATES, get_domain_trust_score

CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

class HttpRetriever(BaseRetriever):
    """Retrieves content using HTTP requests with ddgs search and intent guardrails."""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
    def _get_cache_path(self, url: str) -> str:
        """Get cache file path for URL."""
        hash_digest = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(CACHE_DIR, f"{hash_digest}.txt")
    
    def _passes_guardrails(self, candidate: UrlCandidate, topic: str) -> bool:
        """
        Priority 1: Enforce Intent Guardrails.
        Returns True if candidate passes title/snippet checks.
        """
        if topic not in INTENT_GUARDRAILS:
            return True # No guardrails for unknown topics
            
        config = INTENT_GUARDRAILS[topic]
        text_content = (candidate.title + " " + candidate.snippet).lower()
        
        # Check Negative Terms (Fail Fast)
        for neg_term in config["negative_terms"]:
            if neg_term in text_content:
                print(f"[GUARDRAIL] Filtered {candidate.url}: contains negative term '{neg_term}'")
                return False
                
        # Check Required Terms (Must have at least N)
        hits = 0
        for req_term in config["required_terms"]:
            if req_term in text_content:
                hits += 1
                
        if hits < config["min_required_hits"]:
            print(f"[GUARDRAIL] Filtered {candidate.url}: insufficient required terms ({hits}/{config['min_required_hits']})")
            return False
            
        return True

    async def search(self, query: str, max_results: int = 8) -> List[UrlCandidate]:
        """
        Search using ddgs with intelligent query rewriting, guardrails, and tiered ranking.
        """
        print(f"[HTTP_RETRIEVER] Searching for: '{query[:60]}...'")
        
        candidates = []
        topic = classify_topic(query)
        print(f"[HTTP_RETRIEVER] Topic classified as: {topic}")
        
        # Helper to execute search
        async def execute_search(search_query: str, source_label: str):
            try:
                # Use executor to run sync ddgs in async context
                # Note: ddgs is sync/async, ensuring async usage would be better but this works
                ddgs = DDGS()
                results = ddgs.text(search_query, max_results=max_results) 
                # If ddgs is strictly sync in this version, wrap it. 
                # Assuming current installed version supports simple iteration or is fast enough.
                
                new_candidates = []
                if results:
                    for r in results:
                        if isinstance(r, dict) and 'href' in r:
                            cand = UrlCandidate(
                                url=r['href'],
                                title=r.get('title', 'No title'),
                                snippet=r.get('body', '')
                            )
                            # Apply Guardrails immediately
                            if self._passes_guardrails(cand, topic):
                                new_candidates.append(cand)
                return new_candidates
            except Exception as e:
                print(f"[HTTP_RETRIEVER] Search failed for '{search_query}': {e}")
                return []

        # 1. Targeted Queries (Priority 2)
        # Use specific templates for the topic (e.g. "x vendor", "x api")
        queries_to_try = [query]
        if topic in QUERY_TEMPLATES:
            # Add one or two specific rewrites
            base_terms = query
            # Simple extraction of core noun phrase could make this better, 
            # for now, use query as base if short, or topic keywords if long
            if len(query.split()) > 5:
                # Fallback to key terms from seeds logic logic or simple truncation
                base_terms = " ".join(query.split()[:4])
                
            for template in QUERY_TEMPLATES[topic][:2]: # Try top 2 templates
                queries_to_try.append(template.format(base_query=base_terms))
                
        # Execute searches
        for q in queries_to_try:
            results = await asyncio.to_thread(lambda: list(DDGS().text(q, max_results=max_results))) # Run in thread to be safe
            
            if results:
                for r in results:
                    if isinstance(r, dict) and 'href' in r:
                        cand = UrlCandidate(
                            url=r['href'],
                            title=r.get('title', 'No title'),
                            snippet=r.get('body', '')
                        )
                        if self._passes_guardrails(cand, topic):
                            # Avoid duplicates
                            if not any(c.url == cand.url for c in candidates):
                                candidates.append(cand)

            if len(candidates) >= max_results:
                break
                
        # 2. Simplified fallback
        if not candidates and len(query.split()) > 5:
            simplified = " ".join(query.split()[:4])
            print(f"[HTTP_RETRIEVER] Fallback to simplified: '{simplified}'")
            results = await asyncio.to_thread(lambda: list(DDGS().text(simplified, max_results=max_results)))
            if results:
                 for r in results:
                    if isinstance(r, dict) and 'href' in r:
                        cand = UrlCandidate(
                            url=r['href'],
                            title=r.get('title', 'No title'),
                            snippet=r.get('body', '')
                        )
                        if self._passes_guardrails(cand, topic):
                             if not any(c.url == cand.url for c in candidates):
                                candidates.append(cand)

        # 3. Last Resort: Topic-Gated Seeds
        if not candidates and topic != "unknown":
            print(f"[RETRIEVER] mode=seed_fallback topic={topic}")
            seed_urls = get_seeds_for_topic(topic)
            for url in seed_urls[:max_results]:
                 candidates.append(UrlCandidate(
                    url=url,
                    title=f"Seed Source: {url}",
                    snippet=f"Official seed for {topic}"
                ))
        
        # Priority 3: Tiered Ranking
        # Sort candidates by Domain Trust Score
        candidates.sort(key=lambda c: get_domain_trust_score(c.url), reverse=True)
        
        print(f"[RETRIEVER] Final candidates: {len(candidates)}")
        return candidates[:max_results]
    
    async def fetch(self, url: str) -> Optional[Document]:
        """Fetch URL using HTTP and extract text with trafilatura."""
        
        # Check cache first
        cache_path = self._get_cache_path(url)
        if os.path.exists(cache_path):
            print(f"[HTTP_RETRIEVER] Cache hit: {url}")
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read()
            return Document(
                url=url,
                title="Cached Content",
                text=content,
                text_length=len(content),
                retrieval_method="cache"
            )
        
        print(f"[HTTP_RETRIEVER] Fetching: {url}")
        html_content = ""
        
        # Try httpx first
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=True) as client:
                resp = await client.get(url, headers=self.headers)
                resp.raise_for_status()
                html_content = resp.text
        except Exception as e:
            print(f"[HTTP_RETRIEVER] Httpx failed: {e}. Trying requests...")
            try:
                import requests
                resp = requests.get(url, headers=self.headers, timeout=15, verify=True)
                resp.raise_for_status()
                html_content = resp.text
            except Exception as e2:
                print(f"[HTTP_RETRIEVER] Requests failed: {e2}")
                return None
        
        # Extract text
        try:
            extracted = trafilatura.extract(html_content, include_comments=False, include_tables=True)
            
            if extracted and len(extracted) > 200:
                # Cache it
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(extracted)
                
                return Document(
                    url=url,
                    title="Extracted Content",
                    text=extracted,
                    text_length=len(extracted),
                    raw_html=html_content[:1000],
                    retrieval_method="http"
                )
            else:
                print(f"[HTTP_RETRIEVER] Content too thin: {url}")
                return None
        except Exception as e:
            print(f"[HTTP_RETRIEVER] Extraction failed: {e}")
            return None

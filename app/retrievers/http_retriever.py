"""
HTTP-based retriever with robust search using ddgs.
"""
import httpx
import trafilatura
import hashlib
import os
from typing import List, Optional
from ddgs import DDGS
from .base import BaseRetriever, Document, UrlCandidate
from app.seeds import classify_topic, get_seeds_for_topic, rewrite_query_for_search

CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

class HttpRetriever(BaseRetriever):
    """Retrieves content using HTTP requests with ddgs search."""
    
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
    
    async def search(self, query: str, max_results: int = 8) -> List[UrlCandidate]:
        """
        Search using ddgs with intelligent query rewriting and fallback.
        """
        print(f"[HTTP_RETRIEVER] Searching for: '{query[:60]}...'")
        
        candidates = []
        topic = classify_topic(query)
        print(f"[HTTP_RETRIEVER] Topic: {topic}")
        
        # 1. Try ddgs search with original query
        try:
            ddgs = DDGS()
            results = ddgs.text(query, max_results=max_results)
            if results:
                for r in results:
                    if isinstance(r, dict) and 'href' in r:
                        candidates.append(UrlCandidate(
                            url=r['href'],
                            title=r.get('title', 'No title'),
                            snippet=r.get('body', '')
                        ))
                
                if candidates:
                    print(f"[RETRIEVER] mode=ddgs_search urls={len(candidates)}")
                    return candidates
        except Exception as e:
            print(f"[HTTP_RETRIEVER] ddgs search failed: {e}")
        
        # 2. Try with rewritten query (keyword-focused)
        if not candidates and topic != "unknown":
            rewritten = rewrite_query_for_search(query, topic)
            print(f"[HTTP_RETRIEVER] Retrying with rewritten query: '{rewritten[:60]}...'")
            try:
                ddgs = DDGS()
                results = ddgs.text(rewritten, max_results=max_results)
                if results:
                    for r in results:
                        if isinstance(r, dict) and 'href' in r:
                            candidates.append(UrlCandidate(
                                url=r['href'],
                                title=r.get('title', 'No title'),
                                snippet=r.get('body', '')
                            ))
                    
                    if candidates:
                        print(f"[RETRIEVER] mode=ddgs_search_rewritten urls={len(candidates)}")
                        return candidates
            except Exception as e:
                print(f"[HTTP_RETRIEVER] Rewritten search failed: {e}")
        
        # 3. Try simplified query (first 5 words)
        if not candidates:
            simplified = " ".join(query.split()[:5])
            print(f"[HTTP_RETRIEVER] Retrying with simplified: '{simplified}'")
            try:
                ddgs = DDGS()
                results = ddgs.text(simplified, max_results=max_results)
                if results:
                    for r in results:
                        if isinstance(r, dict) and 'href' in r:
                            candidates.append(UrlCandidate(
                                url=r['href'],
                                title=r.get('title', 'No title'),
                                snippet=r.get('body', '')
                            ))
                    
                    if candidates:
                        print(f"[RETRIEVER] mode=ddgs_search_simplified urls={len(candidates)}")
                        return candidates
            except Exception as e:
                print(f"[HTTP_RETRIEVER] Simplified search failed: {e}")
        
        # 4. Topic-gated seed fallback (LAST RESORT)
        if topic == "unknown":
            print(f"[RETRIEVER] mode=seed_fallback blocked (topic unknown)")
            return []
        
        # Use topic-specific seeds
        seed_urls = get_seeds_for_topic(topic)
        print(f"[RETRIEVER] mode=seed_fallback topic={topic} urls={len(seed_urls)}")
        
        for url in seed_urls[:max_results]:
            candidates.append(UrlCandidate(
                url=url,
                title=f"Seed: {url.split('/')[-1]}",
                snippet=f"Fallback seed for {topic}"
            ))
        
        return candidates
    
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

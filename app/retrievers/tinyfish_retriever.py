"""
TinyFish-based retriever for agentic web browsing.
Handles JS-heavy sites and provides browsing traces.
"""
import os
import agentql
from playwright.async_api import async_playwright
from typing import List, Optional
from .base import BaseRetriever, Document, UrlCandidate
from .http_retriever import HttpRetriever

class TinyFishRetriever(BaseRetriever):
    """
    Retrieves content using TinyFish (AgentQL + Playwright) browser automation.
    Falls back to HttpRetriever on failure.
    """
    
    def __init__(self):
        self.http_fallback = HttpRetriever()
        self.trace_log = []  # Store browsing actions for UI
        self.api_key = os.getenv("AGENTQL_API_KEY")
        
        if not self.api_key:
            print("[TINYFISH] Warning: AGENTQL_API_KEY not set, will use HTTP fallback")
        
    async def search(self, query: str, max_results: int = 5) -> List[UrlCandidate]:
        """
        Search using TinyFish browser (opens DuckDuckGo and extracts results).
        Falls back to HTTP retriever if TinyFish unavailable.
        """
        print(f"[TINYFISH] Searching for: {query[:50]}...")
        
        if not self.api_key:
            print("[TINYFISH] No API key, using HTTP fallback")
            return await self.http_fallback.search(query, max_results)
        
        try:
            search_url = f"https://lite.duckduckgo.com/lite/?q={query.replace(' ', '+')}"
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                )
                page = await context.new_page()
                
                # Navigate to search
                await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000)
                
                # Extract search results
                results = await page.evaluate("""
                    () => {
                        const candidates = [];
                        // DDG Lite uses simple table structure
                        const links = document.querySelectorAll('a.result-link');
                        
                        for (const link of links) {
                            const url = link.href;
                            const title = link.textContent.trim();
                            
                            if (url && url.startsWith('http') && !url.includes('duckduckgo.com')) {
                                candidates.push({
                                    url: url,
                                    title: title,
                                    snippet: ''
                                });
                            }
                        }
                        return candidates;
                    }
                """)
                
                await browser.close()
                
                url_candidates = []
                for r in results[:max_results]:
                    url_candidates.append(UrlCandidate(
                        url=r['url'],
                        title=r['title'],
                        snippet=r['snippet']
                    ))
                
                self.trace_log.append({
                    "action": "search",
                    "query": query,
                    "results_count": len(url_candidates)
                })
                
                if url_candidates:
                    print(f"[TINYFISH] Found {len(url_candidates)} search results")
                    return url_candidates
                else:
                    print("[TINYFISH] No results found, using HTTP fallback")
                    return await self.http_fallback.search(query, max_results)
            
        except Exception as e:
            print(f"[TINYFISH] Search failed: {e}, falling back to HTTP")
            return await self.http_fallback.search(query, max_results)
    
    async def fetch(self, url: str) -> Optional[Document]:
        """
        Fetch URL using TinyFish browser (JS-rendered with AgentQL).
        Falls back to HTTP on failure.
        """
        print(f"[TINYFISH] Opening URL: {url}")
        
        if not self.api_key:
            print("[TINYFISH] No API key, using HTTP fallback")
            return await self.http_fallback.fetch(url)
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                )
                
                # Wrap page with AgentQL for enhanced extraction
                page = await agentql.wrap_async(await context.new_page())
                
                # Navigate and wait for content
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)
                
                # Extract title
                title = await page.title()
                
                # Scroll to load lazy content
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
                
                # Extract main text content
                text = await page.evaluate("document.body.innerText")
                
                await browser.close()
                
                if not text or len(text) < 200:
                    print(f"[TINYFISH] Content too thin ({len(text)} chars), using HTTP fallback")
                    return await self.http_fallback.fetch(url)
                
                doc = Document(
                    url=url,
                    title=title,
                    text=text,
                    text_length=len(text),
                    retrieval_method="tinyfish"
                )
                
                self.trace_log.append({
                    "action": "fetch",
                    "url": url,
                    "method": "tinyfish",
                    "text_length": len(text)
                })
                
                print(f"[TINYFISH] Successfully extracted {len(text)} chars from {url}")
                return doc
            
        except Exception as e:
            print(f"[TINYFISH] Fetch failed for {url}: {e}, using HTTP fallback")
            return await self.http_fallback.fetch(url)
    
    def get_trace_log(self) -> List[dict]:
        """Get browsing trace for UI display."""
        return self.trace_log
    
    def clear_trace_log(self):
        """Clear trace log."""
        self.trace_log = []

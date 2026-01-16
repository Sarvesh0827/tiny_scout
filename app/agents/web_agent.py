"""
Refactored WebAgent with topic-aware relevance scoring.
"""
import asyncio
import logging
from typing import List
from app.models import ResearchTask, ResearchFinding
from app.seeds import classify_topic, get_keywords_for_topic
from app.retrievers import get_retriever, Document

logger = logging.getLogger(__name__)

class WebAgent:
    def __init__(self):
        self.retriever = get_retriever()
        self.trace_log = []
        
    def _score_relevance(self, content: str, topic: str) -> int:
        """Scores content based on topic-specific keywords."""
        keywords = get_keywords_for_topic(topic)
        if not keywords:
            # Generic scoring if no topic keywords
            return len(content) // 100  # Rough score based on length
        
        score = 0
        content_lower = content.lower()
        for kw in keywords:
            score += content_lower.count(kw)
        return score
    
    async def execute_task(self, task: ResearchTask) -> ResearchFinding:
        """
        Executes research task with topic-aware retrieval and scoring.
        """
        print(f"--- WEB AGENT: Processing '{task.description}' ---")
        
        # Classify topic
        topic = classify_topic(task.description)
        print(f"[WEB_AGENT] Topic classified as: {topic}")
        
        # 1. Search for URLs
        url_candidates = await self.retriever.search(task.description, max_results=8)
        
        if not url_candidates:
            print(f"[WEB_AGENT] No URLs found - returning insufficient evidence")
            return ResearchFinding(
                source_url="N/A",
                content="Insufficient evidence: No relevant sources found for this query.",
                relevance_score=0.0,
                extracted_data={"error": "no_sources_found", "topic": topic}
            )
        
        urls = [candidate.url for candidate in url_candidates]
        print(f"[WEB_AGENT] Found {len(urls)} URLs to fetch")
        
        # 2. Fetch documents in parallel
        documents = await self.retriever.fetch_many(urls)
        print(f"[WEB_AGENT] Successfully fetched {len(documents)} documents")
        
        if not documents:
            print(f"[WEB_AGENT] No documents extracted - returning insufficient evidence")
            return ResearchFinding(
                source_url="N/A",
                content="Insufficient evidence: Could not extract content from sources.",
                relevance_score=0.0,
                extracted_data={"error": "extraction_failed", "topic": topic}
            )
        
        # Log retrieval methods
        for doc in documents:
            self.trace_log.append({
                "url": doc.url,
                "method": doc.retrieval_method,
                "text_length": doc.text_length,
                "title": doc.title
            })
        
        # 3. Score and rank documents (topic-aware)
        scored_docs = []
        for doc in documents:
            score = self._score_relevance(doc.text, topic)
            scored_docs.append((doc, score))
        
        # Sort by relevance score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # 4. Select top K documents
        top_k = 3
        top_docs = scored_docs[:top_k]
        
        # Check if we have meaningful content
        total_score = sum(score for _, score in top_docs)
        if total_score == 0:
            print(f"[WEB_AGENT] All documents scored 0 relevance - topic mismatch")
            return ResearchFinding(
                source_url="N/A",
                content=f"Insufficient evidence: Retrieved sources do not match query topic ({topic}).",
                relevance_score=0.0,
                extracted_data={"error": "topic_mismatch", "topic": topic}
            )
        
        # 5. Combine top documents
        combined_text = ""
        urls_list = []
        for doc, score in top_docs:
            truncated = doc.text[:3000]
            combined_text += f"\n\n=== SOURCE: {doc.url} (Score: {int(score)}, Method: {doc.retrieval_method}) ===\n{truncated}"
            urls_list.append(doc.url)
        
        print(f"[WEB_AGENT] Final selection: {len(top_docs)} sources, total relevance: {int(total_score)}")
        
        return ResearchFinding(
            source_url="Multiple Sources",
            content=combined_text,
            relevance_score=1.0,
            extracted_data={
                "source_count": len(top_docs),
                "urls": urls_list,
                "retrieval_methods": [doc.retrieval_method for doc, _ in top_docs],
                "topic": topic,
                "total_relevance_score": int(total_score)
            }
        )
    
    def get_trace_log(self) -> List[dict]:
        """Get browsing trace for UI."""
        return self.trace_log
    
    def clear_trace_log(self):
        """Clear trace log."""
        self.trace_log = []

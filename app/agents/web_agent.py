"""
Refactored WebAgent with topic-aware relevance scoring and tiered ranking.
"""
import asyncio
import logging
from typing import List, Tuple
from app.models import ResearchTask, ResearchFinding
from app.seeds import classify_topic, get_keywords_for_topic
from app.retrievers import get_retriever, Document
from app.config.search_config import get_domain_trust_score

logger = logging.getLogger(__name__)

class WebAgent:
    def __init__(self):
        self.retriever = get_retriever()
        self.trace_log = []
        
    def _score_content_relevance(self, content: str, topic: str) -> float:
        """Scores content based on topic-specific keywords (0.0 to 1.0)."""
        keywords = get_keywords_for_topic(topic)
        if not keywords:
            return min(len(content) / 5000, 1.0) # Fallback based on length
        
        content_lower = content.lower()
        hits = 0
        for kw in keywords:
            hits += content_lower.count(kw)
        
        # Normalize: 10 hits = 1.0
        return min(hits / 10.0, 1.0)
    
    async def execute_task(self, task: ResearchTask, logger=None) -> ResearchFinding:
        """
        Executes research task with topic-aware retrieval and tiered ranking.
        """
        print(f"--- WEB AGENT: Processing '{task.description}' ---")
        
        # Classify topic
        topic = classify_topic(task.description)
        print(f"[WEB_AGENT] Topic classified as: {topic}")
        
        if logger:
            logger.log('web_agent', f"Processing task: {task.description}", 
                      payload={'task_id': task.id, 'topic': topic})
            logger.set_topic(topic)
        
        # 1. Search for URLs
        url_candidates = await self.retriever.search(task.description, max_results=8)
        
        if not url_candidates:
            print(f"[WEB_AGENT] No URLs found - returning insufficient evidence")
            if logger:
                logger.log('web_agent', 'No URLs found', level='warn',
                          payload={'reason': 'no_sources_found', 'task': task.description})
            return ResearchFinding(
                source_url="N/A",
                content="Insufficient evidence: No relevant sources found for this query.",
                relevance_score=0.0,
                extracted_data={"error": "no_sources_found", "topic": topic}
            )
        
        urls = [candidate.url for candidate in url_candidates]
        print(f"[WEB_AGENT] Found {len(urls)} URLs to fetch")
        
        if logger:
            logger.log('web_agent', f'Found {len(urls)} URLs', 
                      payload={'url_count': len(urls), 'urls': urls[:5]})  # Log first 5
        
        # 2. Fetch documents in parallel
        documents = await self.retriever.fetch_many(urls)
        print(f"[WEB_AGENT] Successfully fetched {len(documents)} documents")
        
        if not documents:
            print(f"[WEB_AGENT] No documents extracted - returning insufficient evidence")
            if logger:
                logger.log('web_agent', 'Document extraction failed', level='error',
                          payload={'reason': 'extraction_failed', 'url_count': len(urls)})
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
        
        # 3. Tiered Ranking (Priority 3)
        # Final Score = 0.6 * Content Relevance + 0.4 * Domain Trust
        scored_docs: List[Tuple[Document, float, float, float]] = []
        
        for doc in documents:
            content_score = self._score_content_relevance(doc.text, topic)
            trust_score = get_domain_trust_score(doc.url)
            
            final_score = (0.6 * content_score) + (0.4 * trust_score)
            scored_docs.append((doc, final_score, content_score, trust_score))
            
            # Log each document to database
            if logger:
                logger.log_document(
                    task=task.description,
                    url=doc.url,
                    retrieval_method=doc.retrieval_method,
                    content_len=doc.text_length,
                    http_status=200,  # Assume success if we got content
                    title=doc.title,
                    relevance_score=content_score,
                    tier=self._get_tier_from_trust(trust_score),
                    selected=False,  # Will update later for selected docs
                    snippet=doc.text[:500] if doc.text else None
                )
        
        # Sort by final score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # 4. Select Top K
        # Enforce minimum quality: Filter truly irrelevant docs (< 0.2)
        top_docs = [x for x in scored_docs if x[1] > 0.15][:3]
        
        if not top_docs:
            print(f"[WEB_AGENT] All documents below quality threshold")
            if logger:
                logger.log('web_agent', 'All documents below quality threshold', level='warn',
                          payload={'reason': 'low_relevance', 'topic': topic, 'doc_count': len(scored_docs)})
            return ResearchFinding(
                source_url="N/A",
                content=f"Insufficient evidence: Sources retrieved but low relevance for topic ({topic}).",
                relevance_score=0.0,
                extracted_data={"error": "low_relevance", "topic": topic}
            )
        
        # Update selected status in database
        if logger:
            selected_urls = [doc[0].url for doc in top_docs]
            logger.log('web_agent', f'Selected {len(top_docs)} documents', 
                      payload={
                          'selected_count': len(top_docs),
                          'selected_urls': selected_urls,
                          'scores': [{'url': d[0].url, 'final_score': d[1], 
                                     'content_score': d[2], 'trust_score': d[3]} 
                                    for d in top_docs]
                      })
        
        # 5. Combine Evidence
        combined_text = ""
        urls_list = []
        total_score_accum = 0.0
        
        for doc, f_score, c_score, t_score in top_docs:
            truncated = doc.text[:3000]
            # Add metadata block for the Synthesizer to use
            combined_text += f"\n\n=== SOURCE START ===\nURL: {doc.url}\nTRUST_SCORE: {t_score}\nRELEVANCE: {c_score:.2f}\nCONTENT:\n{truncated}\n=== SOURCE END ==="
            urls_list.append(doc.url)
            total_score_accum += f_score
            
        avg_score = total_score_accum / len(top_docs)
        print(f"[WEB_AGENT] Final selection: {len(top_docs)} docs, avg score: {avg_score:.2f}")
        
        return ResearchFinding(
            source_url="Multiple Sources",
            content=combined_text,
            relevance_score=avg_score,
            extracted_data={
                "source_count": len(top_docs),
                "urls": urls_list,
                "retrieval_methods": [d[0].retrieval_method for d in top_docs],
                "topic": topic,
                "avg_score": avg_score
            }
        )
    
    def _get_tier_from_trust(self, trust_score: float) -> str:
        """Convert trust score to tier."""
        if trust_score >= 0.9:
            return 'A'
        elif trust_score >= 0.6:
            return 'B'
        elif trust_score >= 0.3:
            return 'C'
        else:
            return 'unknown'
    
    def get_trace_log(self) -> List[dict]:
        """Get browsing trace for UI."""
        return self.trace_log
    
    def clear_trace_log(self):
        """Clear trace log."""
        self.trace_log = []

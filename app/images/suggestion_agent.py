"""
LLM-based agent for suggesting images to generate.
"""
import json
import os
from typing import Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from .models import ImageSuggestion, ImageRequest

load_dotenv()

class ImageSuggestionAgent:
    """Agent that suggests images to generate for a research report."""
    
    def __init__(self, model_name: Optional[str] = None):
        if model_name is None:
            model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        
        self.llm = ChatAnthropic(
            model=model_name,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.3,
            max_tokens=2048
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at suggesting visual aids for research reports.

RULES:
1. Only suggest images if they ADD REAL VALUE (diagrams, comparisons, timelines, landscapes).
2. Do NOT suggest images for:
   - Simple factual Q&A
   - Sensitive medical/political content
   - Anything requesting real people
   - Reports with < 2 sections
3. Max 3 images per report.
4. Prompts must be detailed, avoid brand logos and copyrighted characters.
5. Return STRICT JSON only, no markdown, no prose.

JSON Format:
{{
  "should_generate": true/false,
  "reasoning": "why or why not",
  "images": [
    {{
      "title": "Short title",
      "rationale": "Why this visual helps",
      "prompt": "Detailed Freepik prompt (infographic style, clean, professional...)",
      "aspect_ratio": "16:9"
    }}
  ]
}}

Aspect ratios: "1:1", "16:9", "9:16", "4:3"
"""),
            ("user", """Research Query: {query}

Report Outline:
{outline}

Summary:
{summary}

Should we generate visuals? If yes, suggest up to 3.""")
        ])
        
        self.chain = self.prompt | self.llm
    
    async def suggest_images(
        self,
        query: str,
        report_outline: str,
        summary: str
    ) -> ImageSuggestion:
        """
        Ask LLM to suggest images for the report.
        """
        print(f"[IMAGE_SUGGEST] Analyzing report for visual opportunities...")
        
        try:
            response = await self.chain.ainvoke({
                "query": query,
                "outline": report_outline,
                "summary": summary
            })
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON
            data = self._extract_json(content)
            
            if not data:
                print("[IMAGE_SUGGEST] Failed to parse JSON, defaulting to no images")
                return ImageSuggestion(should_generate=False, images=[], reasoning="Parse error")
            
            # Convert to ImageSuggestion
            should_generate = data.get("should_generate", False)
            reasoning = data.get("reasoning", "")
            
            images = []
            for img_data in data.get("images", [])[:3]:  # Max 3
                images.append(ImageRequest(
                    title=img_data.get("title", "Untitled"),
                    prompt=img_data.get("prompt", ""),
                    rationale=img_data.get("rationale", ""),
                    aspect_ratio=img_data.get("aspect_ratio", "16:9")
                ))
            
            print(f"[IMAGE_SUGGEST] Suggestion: generate={should_generate}, count={len(images)}")
            
            return ImageSuggestion(
                should_generate=should_generate,
                images=images,
                reasoning=reasoning
            )
            
        except Exception as e:
            print(f"[IMAGE_SUGGEST] Error: {e}")
            return ImageSuggestion(should_generate=False, images=[], reasoning=f"Error: {e}")
    
    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from LLM response."""
        import re
        
        # Try to find JSON between first { and last }
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_str = text[first_brace:last_brace+1]
            try:
                return json.loads(json_str)
            except:
                pass
        
        # Try whole text
        try:
            return json.loads(text)
        except:
            pass
        
        # Try code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        return None

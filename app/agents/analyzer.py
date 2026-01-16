from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
import json
import os
from dotenv import load_dotenv

load_dotenv()
from app.state import AgentState

class AnalyzerAgent:
    def __init__(self, model_name=None):
        if model_name is None:
            model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        
        self.model_name = model_name
        self.fallback_model = "claude-haiku-4-5"
        
        try:
            self.llm = ChatAnthropic(
                model=model_name,
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                temperature=0.3,
                max_tokens=4096
            )
            print(f"[ANALYZER] Using model: {model_name}")
        except Exception as e:
            print(f"[ANALYZER] Model {model_name} failed, falling back to {self.fallback_model}: {e}")
            self.llm = ChatAnthropic(
                model=self.fallback_model,
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                temperature=0.3,
                max_tokens=4096
            )
            self.model_name = self.fallback_model
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert research analyst. You will be given a research goal and some raw text found on a website. "
                       "Your job is to extract relevant information, specifically looking for numerical data, pricing, features, or contradictory info. "
                       "If the text is irrelevant, say so."),
            ("user", "Goal: {goal}\n\nRaw Content: {content}")
        ])
        
        self.chain = self.prompt | self.llm

    async def analyze(self, content: str, goal: str) -> str:
        response = await self.chain.ainvoke({"goal": goal, "content": content[:5000]}) # Truncate for context limit
        return response.content

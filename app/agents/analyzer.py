from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from app.state import AgentState

class AnalyzerAgent:
    def __init__(self, model_name="mistral"):
        self.llm = ChatOllama(model=model_name, temperature=0)
        
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

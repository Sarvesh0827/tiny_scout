from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.models import ResearchPlan, ResearchTask
from app.state import AgentState
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

class PlannerAgent:
    def __init__(self, model_name=None):
        if model_name is None:
            model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        
        self.model_name = model_name
        self.fallback_model = "claude-haiku-4-5"
        
        try:
            self.llm = ChatAnthropic(
                model=model_name,
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                temperature=0.7,
                max_tokens=4096
            )
            print(f"[PLANNER] Using model: {model_name}")
        except Exception as e:
            print(f"[PLANNER] Model {model_name} failed, falling back to {self.fallback_model}: {e}")
            self.llm = ChatAnthropic(
                model=self.fallback_model,
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                temperature=0.7,
                max_tokens=4096
            )
            self.model_name = self.fallback_model
        
        self.parser = PydanticOutputParser(pydantic_object=ResearchPlan)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert research planner. breakdown the user's research question into actionable web research tasks. "
                       "Return a JSON object with a 'main_goal' and a list of 'tasks'. Each task should have a clear description. "
                       "LIMIT the number of tasks to 3-5 for now to ensure speed."),
            ("user", "{query}")
        ])
        
        self.chain = self.prompt | self.llm 

    async def plan(self, state: AgentState) -> dict:
        """
        Invokes the planner to generate a list of tasks.
        """
        print(f"--- PLANNER: Planning for query: {state['query']} ---")
        
        # We invoke the LLM. 
        # Note: ChatOllama with format="json" ensures we get JSON. 
        # However, we might need to parse it carefully if the model is chatty.
        response = await self.chain.ainvoke({"query": state['query']})
        
        # In a real impl, we'd add robust parsing here. 
        # For this hackathon scope, we assume the model obeys the JSON instruction or we do simple parsing.
        
        import json
        try:
            # content might be a string or already a dict/object depending on langchain version/config
            content_str = response.content if hasattr(response, 'content') else str(response)
            data = json.loads(content_str)
            
            # Convert to internal model
            tasks = []
            for t in data.get("tasks", []):
                tasks.append(ResearchTask(
                    id=str(uuid.uuid4()),
                    description=t.get("description", str(t)),
                    status="pending"
                ))
            
            return {"plan": tasks, "messages": ["Planner generated tasks."]}
            
        except Exception as e:
            print(f"Error parsing plan: {e}")
            # Fallback plan
            return {
                "plan": [ResearchTask(id=str(uuid.uuid4()), description=f"Research {state['query']}", status="pending")],
                "messages": [f"Planner error: {e}. using fallback."]
            }

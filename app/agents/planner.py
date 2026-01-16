from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.models import ResearchPlan, ResearchTask
from app.state import AgentState
import uuid

class PlannerAgent:
    def __init__(self, model_name="mistral"):
        self.llm = ChatOllama(model=model_name, temperature=0, format="json")
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

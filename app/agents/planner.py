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
            ("system", "You are an expert research planner. Break down the user's research question into 3-5 actionable web research tasks. "
                       "IMPORTANT: Return ONLY valid JSON with NO markdown formatting, NO code blocks, NO prose. "
                       "Format: {\"main_goal\": \"...\", \"tasks\": [{\"description\": \"...\"}, ...]}"),
            ("user", "{query}")
        ])
        
        self.chain = self.prompt | self.llm 

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from response, handling markdown and prose."""
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
        
        # If that fails, try the whole text
        try:
            return json.loads(text)
        except:
            pass
        
        # Last resort: look for JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        return None

    async def plan(self, state: AgentState) -> dict:
        """
        Invokes the planner to generate a list of tasks.
        """
        print(f"--- PLANNER: Planning for query: {state['query']} ---")
        
        # Invoke LLM
        response = await self.chain.ainvoke({"query": state['query']})
        
        # Extract content
        content_str = response.content if hasattr(response, 'content') else str(response)
        
        # Try to parse JSON with robust extraction
        data = self._extract_json(content_str)
        
        if not data:
            print(f"[PLANNER] JSON parse failed, retrying with explicit instruction...")
            # Retry once with more explicit prompt
            retry_response = await self.llm.ainvoke(
                f"Convert this research question into JSON format with main_goal and tasks array. "
                f"Return ONLY the JSON object, nothing else: {state['query']}"
            )
            retry_content = retry_response.content if hasattr(retry_response, 'content') else str(retry_response)
            data = self._extract_json(retry_content)
        
        if not data:
            print(f"[PLANNER] JSON parse still failed, using fallback single task")
            # Fallback: create a single task
            return {
                "plan": [ResearchTask(
                    id=str(uuid.uuid4()),
                    description=state['query'],
                    status="pending"
                )],
                "messages": ["Planner used fallback (JSON parse failed)"]
            }
        
        # Convert to internal model
        try:
            tasks = []
            for t in data.get("tasks", []):
                task_desc = t.get("description") if isinstance(t, dict) else str(t)
                tasks.append(ResearchTask(
                    id=str(uuid.uuid4()),
                    description=task_desc,
                    status="pending"
                ))
            
            if not tasks:
                # If no tasks, use the query itself
                tasks = [ResearchTask(
                    id=str(uuid.uuid4()),
                    description=state['query'],
                    status="pending"
                )]
            
            print(f"[PLANNER] Generated {len(tasks)} tasks")
            return {"plan": tasks, "messages": ["Planner generated tasks."]}
            
        except Exception as e:
            print(f"[PLANNER] Error processing tasks: {e}")
            return {
                "plan": [ResearchTask(
                    id=str(uuid.uuid4()),
                    description=state['query'],
                    status="pending"
                )],
                "messages": [f"Planner error: {e}. Using fallback."]
            }

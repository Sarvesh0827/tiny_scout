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
        
        # Priority 5: Robust List Format by default
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert research planner. Break down the user's research question into 4-6 specific search queries.\n"
                       "IMPORTANT: Return ONLY a numbered list of queries. One query per line.\n"
                       "Do not use JSON. Do not include introductory text."),
            ("user", "{query}")
        ])
        
        self.chain = self.prompt | self.llm 

    async def plan(self, state: AgentState) -> dict:
        """
        Invokes the planner to generate a list of tasks using robust list parsing.
        """
        logger = state.get('logger')
        
        if logger:
            logger.log('planner', f"Planning started for query: {state['query']}", 
                      payload={'query': state['query'], 'model': self.model_name})
        
        print(f"--- PLANNER: Planning for query: {state['query']} ---")
        
        try:
            # Invoke LLM
            response = await self.chain.ainvoke({"query": state['query']})
            content_str = response.content if hasattr(response, 'content') else str(response)
            
            if logger:
                logger.log('planner', 'Raw LLM response received', level='debug',
                          payload={'raw_response': content_str[:500], 'length': len(content_str)})
            
            # Parse list format
            tasks = []
            for line in content_str.split('\n'):
                line = line.strip()
                import re
                # Remove Markdown list bullets and numbers (1., -, *, etc.)
                cleaned = re.sub(r'^[\d\.\-\*\)]+\s*', '', line)
                if cleaned and len(cleaned) > 10:  # Meaningful query
                     tasks.append(ResearchTask(
                        id=str(uuid.uuid4()),
                        description=cleaned,
                        status="pending"
                    ))
            
            if not tasks:
                if logger:
                    logger.log('planner', 'List parsing yielded no tasks, using fallback', level='warn')
                print(f"[PLANNER] List parsing yielded no tasks, using fallback.")
                tasks = [ResearchTask(
                    id=str(uuid.uuid4()),
                    description=state['query'],
                    status="pending"
                )]
            
            if logger:
                logger.log('planner', f'Generated {len(tasks)} tasks', 
                          payload={'task_count': len(tasks), 
                                  'tasks': [t.description for t in tasks]})
            
            print(f"[PLANNER] Generated {len(tasks)} tasks")
            return {"plan": tasks, "messages": ["Planner generated tasks (List Mode)."]}
            
        except Exception as e:
            if logger:
                logger.log('planner', f'Error generating plan: {str(e)}', level='error',
                          payload={'error': str(e), 'error_type': type(e).__name__})
            
            print(f"[PLANNER] Error generating plan: {e}")
            return {
                "plan": [ResearchTask(
                    id=str(uuid.uuid4()),
                    description=state['query'],
                    status="pending"
                )],
                "messages": [f"Planner error: {e}. Using fallback."]
            }

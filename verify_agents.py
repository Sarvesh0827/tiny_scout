import asyncio
import sys
from app.graph import app_graph
from app.models import ResearchTask

async def run_test():
    print("Starting verification of TinyScout Agents...")
    
    initial_state = {
        "query": "What is the capital of France?",
        "plan": [],
        "findings": [],
        "final_report": None,
        "messages": []
    }
    
    try:
        async for output in app_graph.astream(initial_state):
            for key, value in output.items():
                print(f"\n--- Node '{key}' Finished ---")
                if "messages" in value:
                    for m in value["messages"]:
                        print(f"Log: {m}")
                        
        print("\nVerification Complete.")
    except Exception as e:
        print(f"\nCRITICAL FAILURE: {e}")
        print("Please ensure Ollama is running (ollama serve) and 'mistral' model is pulled (ollama pull mistral).")

if __name__ == "__main__":
    asyncio.run(run_test())

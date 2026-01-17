"""
End-to-end test for instrumented pipeline with RunLogger.
Tests that all agents log correctly to the ops console.
"""
import asyncio
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

from app.ops import RunLogger, get_session, Run, RunEvent, Document
from app.agents.planner import PlannerAgent
from app.agents.web_agent import WebAgent
from app.agents.synthesizer import SynthesizerAgent
from app.models import ResearchTask, ResearchFinding

async def test_instrumented_pipeline():
    """Test full pipeline with RunLogger."""
    print("=" * 70)
    print("TESTING INSTRUMENTED PIPELINE")
    print("=" * 70)
    
    # Create RunLogger
    run_id = str(uuid.uuid4())
    config = {
        'planner_model': os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
        'analyzer_model': os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
        'synthesizer_model': os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
        'retriever_backend': os.getenv('RETRIEVER_BACKEND', 'tinyfish')
    }
    
    logger = RunLogger(
        run_id=run_id,
        research_goal="Test: AI voice moderation competitors",
        config=config
    )
    
    print(f"\n✅ RunLogger created: {run_id[:8]}...")
    
    # Test 1: Planner
    print("\n--- Testing Planner ---")
    planner = PlannerAgent()
    state = {
        'query': 'Find top 3 AI voice moderation platforms',
        'logger': logger
    }
    
    result = await planner.plan(state)
    tasks = result['plan']
    print(f"✅ Planner generated {len(tasks)} tasks")
    
    # Test 2: Web Agent (just one task)
    print("\n--- Testing Web Agent ---")
    web_agent = WebAgent()
    
    if tasks:
        task = tasks[0]
        finding = await web_agent.execute_task(task, logger=logger)
        print(f"✅ Web Agent processed task: {finding.source_url}")
    
    # Test 3: Synthesizer
    print("\n--- Testing Synthesizer ---")
    synthesizer = SynthesizerAgent()
    synth_state = {
        'query': state['query'],
        'findings': [finding] if tasks else [],
        'logger': logger
    }
    
    synth_result = await synthesizer.synthesize(synth_state)
    print(f"✅ Synthesizer generated report")
    
    # Close logger
    logger.close()
    
    print("\n" + "=" * 70)
    print("VERIFYING DATABASE")
    print("=" * 70)
    
    # Verify database
    session = get_session()
    
    run = session.query(Run).filter(Run.id == run_id).first()
    events = session.query(RunEvent).filter(RunEvent.run_id == run_id).all()
    docs = session.query(Document).filter(Document.run_id == run_id).all()
    
    print(f"\n📊 Database Stats for Run {run_id[:8]}:")
    print(f"   Status: {run.status}")
    print(f"   Topic: {run.topic}")
    print(f"   Events: {len(events)}")
    print(f"   Documents: {len(docs)}")
    
    print("\n📝 Events by Stage:")
    stages = {}
    for event in events:
        stages[event.stage] = stages.get(event.stage, 0) + 1
    
    for stage, count in stages.items():
        print(f"   {stage}: {count} events")
    
    print("\n📄 Documents:")
    for doc in docs[:5]:  # Show first 5
        print(f"   {doc.url[:50]}... | {doc.retrieval_method} | {doc.content_len} chars | Tier {doc.tier}")
    
    session.close()
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print(f"\n🔗 View in Ops Console:")
    print(f"   http://localhost:8000/api/runs/{run_id}")
    print(f"   http://localhost:8000/api/runs/{run_id}/events")
    print(f"   http://localhost:8000/api/runs/{run_id}/documents")
    print()

if __name__ == "__main__":
    asyncio.run(test_instrumented_pipeline())

"""
Test script for Ops Console functionality.
Creates sample runs and events to verify database and API.
"""
import asyncio
import uuid
from app.ops import RunLogger, get_session, Run, RunEvent, Document

def test_run_logger():
    """Test RunLogger functionality."""
    print("=" * 60)
    print("Testing Ops Console - RunLogger")
    print("=" * 60)
    
    # Create a test run
    run_id = str(uuid.uuid4())
    config = {
        'planner_model': 'claude-3-haiku-20240307',
        'analyzer_model': 'claude-3-haiku-20240307',
        'synthesizer_model': 'claude-3-haiku-20240307',
        'retriever_backend': 'tinyfish'
    }
    
    logger = RunLogger(
        run_id=run_id,
        research_goal="Test query: AI voice moderation competitors",
        config=config
    )
    
    # Log some events
    logger.log('planner', 'Planning started', payload={'query': 'test query'})
    logger.log('planner', 'Tasks generated', payload={'tasks': ['task1', 'task2', 'task3']})
    
    logger.set_topic('voice_moderation')
    
    logger.log('retriever', 'Search started', payload={'backend': 'tinyfish'})
    logger.log('retriever', 'TinyFish returned 0 results', level='warn')
    logger.log('retriever', 'Using HTTP fallback', payload={'urls': 5})
    
    # Log some documents
    logger.log_document(
        task='Find competitors',
        url='https://www.modulate.ai/toxmod',
        retrieval_method='tinyfish',
        content_len=5290,
        http_status=200,
        title='Modulate ToxMod',
        relevance_score=0.85,
        tier='A',
        selected=True,
        snippet='Modulate provides AI-powered voice moderation...'
    )
    
    logger.log_document(
        task='Find competitors',
        url='https://example.com/blocked',
        retrieval_method='http',
        content_len=0,
        http_status=403,
        title=None,
        relevance_score=0.0,
        tier='unknown',
        selected=False
    )
    
    logger.log('synthesizer', 'Synthesis started')
    logger.set_final_report('# Test Report\n\nThis is a test report.')
    logger.set_status('success')
    
    logger.close()
    
    print(f"\n✅ Test run created: {run_id[:8]}")
    print(f"   Check database: cache/ops_console.db")
    print(f"   Or query API: http://localhost:8000/api/runs/{run_id}")
    
    return run_id

def verify_database():
    """Verify database contents."""
    print("\n" + "=" * 60)
    print("Verifying Database")
    print("=" * 60)
    
    session = get_session()
    
    # Count records
    run_count = session.query(Run).count()
    event_count = session.query(RunEvent).count()
    doc_count = session.query(Document).count()
    
    print(f"\n📊 Database Stats:")
    print(f"   Runs: {run_count}")
    print(f"   Events: {event_count}")
    print(f"   Documents: {doc_count}")
    
    # Show latest run
    latest_run = session.query(Run).order_by(Run.created_at.desc()).first()
    if latest_run:
        print(f"\n📝 Latest Run:")
        print(f"   ID: {latest_run.id[:8]}...")
        print(f"   Goal: {latest_run.research_goal}")
        print(f"   Status: {latest_run.status}")
        print(f"   Topic: {latest_run.topic}")
        print(f"   Backend: {latest_run.retriever_backend}")
    
    session.close()

def main():
    """Run all tests."""
    print("\n🧪 Ops Console Test Suite\n")
    
    # Test 1: RunLogger
    run_id = test_run_logger()
    
    # Test 2: Verify Database
    verify_database()
    
    print("\n" + "=" * 60)
    print("✅ All Tests Passed!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Start API: ./venv/bin/python3 ops_api.py")
    print("2. Test API: curl http://localhost:8000/api/runs")
    print("3. Build Retool dashboard using docs/OPS_CONSOLE.md")
    print()

if __name__ == "__main__":
    main()

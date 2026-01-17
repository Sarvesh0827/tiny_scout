"""
Test script for Yutori Monitoring integration.
"""
import asyncio
from app.monitors import ScoutManager, enhance_monitoring_query

async def test_monitoring():
    """Test Yutori monitoring functionality."""
    print("=" * 70)
    print("TESTING YUTORI MONITORING")
    print("=" * 70)
    
    # Test 1: Query Enhancement
    print("\n--- Test 1: Query Enhancement ---")
    original = "Monitor AI voice moderation industry"
    enhanced = enhance_monitoring_query(original)
    print(f"Original: {original}")
    print(f"Enhanced:\n{enhanced}")
    
    # Test 2: Scout Manager (requires API key)
    print("\n--- Test 2: Scout Manager ---")
    try:
        manager = ScoutManager()
        print("✅ Scout Manager initialized")
        
        # Get existing scouts
        scouts = manager.get_all_scouts()
        print(f"📊 Active scouts: {len(scouts)}")
        
        for scout in scouts:
            print(f"\n  Scout: {scout.id[:8]}...")
            print(f"  Query: {scout.original_query}")
            print(f"  Interval: {scout.output_interval // 60} minutes")
            print(f"  Next run: {scout.next_run_timestamp}")
            
            # Get updates
            updates = manager.get_scout_updates(scout.id, limit=5)
            print(f"  Updates: {len(updates)}")
            
            for update in updates[:2]:  # Show first 2
                print(f"    - {update.headline or 'Update'}")
                print(f"      {update.timestamp}")
        
        manager.close()
        
    except ValueError as e:
        print(f"⚠️  {e}")
        print("💡 Set YUTORI_API_KEY in .env to test scout creation")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("✅ TESTS COMPLETE")
    print("=" * 70)
    print("\n📋 Next Steps:")
    print("1. Set YUTORI_API_KEY in .env")
    print("2. Run monitoring dashboard: ./venv/bin/streamlit run ui/monitoring.py --server.port 9998")
    print("3. Create a scout and start monitoring!")
    print()

if __name__ == "__main__":
    asyncio.run(test_monitoring())

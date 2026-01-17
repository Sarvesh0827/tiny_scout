"""
Debug script to test Freepik API directly and see actual responses.
"""
import httpx
import asyncio
import os
import json
from dotenv import load_dotenv

load_dotenv()

async def test_freepik_api():
    """Test Freepik API with actual request."""
    
    api_key = os.getenv("FREEPIK_API_KEY")
    if not api_key:
        print("❌ No FREEPIK_API_KEY found in .env")
        return
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    # Test payload
    payload = {
        "prompt": "A simple flowchart diagram showing 3 steps, clean professional infographic style",
        "negative_prompt": "text, watermark, logo, brand name, copyright, low quality",
        "guidance_scale": 7.5,
        "num_images": 1,
        "image": {
            "size": "landscape"
        }
    }
    
    headers = {
        "x-freepik-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    print("\n📤 Sending request to Freepik API...")
    print(f"Endpoint: https://api.freepik.com/v1/ai/text-to-image")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.freepik.com/v1/ai/text-to-image",
                headers=headers,
                json=payload
            )
            
            print(f"\n📥 Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            try:
                data = response.json()
                print(f"\n📄 Response Body:")
                print(json.dumps(data, indent=2))
                
                # Check for task_id
                if "task_id" in data:
                    print(f"\n✅ Task ID found: {data['task_id']}")
                elif "data" in data and isinstance(data["data"], dict) and "task_id" in data["data"]:
                    print(f"\n✅ Task ID found in data: {data['data']['task_id']}")
                else:
                    print(f"\n⚠️  No task_id found in response")
                    print(f"Available keys: {list(data.keys())}")
                    
            except Exception as e:
                print(f"\n❌ Could not parse JSON: {e}")
                print(f"Raw response: {response.text}")
            
            if response.status_code != 200:
                print(f"\n❌ API returned error status: {response.status_code}")
                
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_freepik_api())

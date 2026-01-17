"""
Test script for image generation module.
Tests suggestion agent and generator (with mock if no API key).
"""
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.images import ImageSuggestionAgent, ImageGenerator, ImageRequest, ImageStatus

async def test_suggestion_agent():
    """Test LLM image suggestion."""
    print("\n=== Testing Image Suggestion Agent ===\n")
    
    agent = ImageSuggestionAgent()
    
    query = "Research the top 5 AI voice moderation competitors"
    outline = """
# Executive Summary
# Key Competitors
## Modulate.ai
## Unity Vivox
## Spectrum Labs
# Comparison Table
"""
    summary = "This report analyzes the top AI voice moderation platforms..."
    
    suggestion = await agent.suggest_images(query, outline, summary)
    
    print(f"Should Generate: {suggestion.should_generate}")
    print(f"Reasoning: {suggestion.reasoning}")
    print(f"Number of Images: {len(suggestion.images)}")
    
    for i, img_req in enumerate(suggestion.images, 1):
        print(f"\nImage {i}:")
        print(f"  Title: {img_req.title}")
        print(f"  Rationale: {img_req.rationale}")
        print(f"  Prompt: {img_req.prompt[:100]}...")
        print(f"  Aspect Ratio: {img_req.aspect_ratio}")

async def test_generator():
    """Test image generator (checks if enabled)."""
    print("\n=== Testing Image Generator ===\n")
    
    generator = ImageGenerator()
    
    if not generator.is_enabled():
        print("⚠️  Image generation disabled (no FREEPIK_API_KEY)")
        print("   Set FREEPIK_API_KEY in .env to test actual generation")
        return
    
    # Create a simple test request
    test_request = ImageRequest(
        title="Test Diagram",
        prompt="Create a simple flowchart showing a 3-step process, clean infographic style, professional",
        rationale="Testing image generation",
        aspect_ratio="16:9"
    )
    
    print(f"Generating test image...")
    artifacts = await generator.generate_images([test_request])
    
    for artifact in artifacts:
        print(f"\nResult:")
        print(f"  Title: {artifact.title}")
        print(f"  Status: {artifact.status.value}")
        
        if artifact.status == ImageStatus.COMPLETED:
            print(f"  URL: {artifact.image_url}")
            print(f"  ✅ Success!")
        elif artifact.status == ImageStatus.FAILED:
            print(f"  Error: {artifact.error_message}")
            print(f"  ❌ Failed")

async def main():
    """Run all tests."""
    print("=" * 60)
    print("TinyScout Image Generation Test Suite")
    print("=" * 60)
    
    # Test 1: Suggestion Agent
    await test_suggestion_agent()
    
    # Test 2: Generator (if API key available)
    await test_generator()
    
    print("\n" + "=" * 60)
    print("Tests Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

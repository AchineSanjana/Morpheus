#!/usr/bin/env python3
"""
Test script to verify Gemini API functionality
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def test_gemini():
    """Test the Gemini API with different models"""
    print("🧪 Testing Gemini API...")
    print(f"API Key present: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")
    
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ No GEMINI_API_KEY found in environment")
        return
    
    from app.llm_gemini import generate_gemini_text
    
    # Test with a simple prompt
    test_prompt = "What is sleep hygiene? Provide 3 key tips."
    
    print(f"\n📝 Test prompt: {test_prompt}")
    print("=" * 50)
    
    try:
        response = await generate_gemini_text(test_prompt)
        if response:
            print("✅ Gemini API working!")
            print(f"Response length: {len(response)} characters")
            print(f"Response preview: {response[:200]}...")
            return True
        else:
            print("❌ Gemini API returned None")
            return False
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

async def test_specific_models():
    """Test specific models individually"""
    from app.llm_gemini import generate_gemini_text
    
    models_to_test = ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]
    simple_prompt = "Hello, how are you?"
    
    print("\n🔍 Testing individual models...")
    print("=" * 50)
    
    for model in models_to_test:
        print(f"\nTesting {model}...")
        try:
            response = await generate_gemini_text(simple_prompt, model_name=model)
            if response:
                print(f"✅ {model}: Working")
            else:
                print(f"❌ {model}: Returned None")
        except Exception as e:
            print(f"❌ {model}: Failed with {e}")

if __name__ == "__main__":
    print("🚀 Starting Gemini API tests...\n")
    
    # Run basic test
    success = asyncio.run(test_gemini())
    
    # Run model-specific tests
    asyncio.run(test_specific_models())
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Basic test passed - Gemini API is working!")
    else:
        print("❌ Basic test failed - Check your API key and network connection")
    print("🏁 Test complete!")
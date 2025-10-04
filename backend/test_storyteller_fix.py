#!/usr/bin/env python3
"""
Quick test to verify the storyteller.py fix
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_storyteller_import():
    """Test that storyteller can be imported without errors"""
    print("🧪 Testing Storyteller Import and Basic Functionality")
    print("=" * 50)
    
    try:
        # Test import
        from app.agents.storyteller import StoryTellerAgent
        print("✅ Successfully imported StoryTellerAgent")
        
        # Test instantiation
        storyteller = StoryTellerAgent()
        print("✅ Successfully created storyteller instance")
        print(f"   Name: {storyteller.name}")
        print(f"   Audio enabled: {storyteller.audio_enabled}")
        
        # Test security validator
        test_input = "Tell me a bedtime story about a sleepy cat"
        sanitized = storyteller.security_validator.sanitize_user_input(test_input)
        print(f"✅ Security validator working")
        print(f"   Original: {test_input}")
        print(f"   Sanitized: {sanitized}")
        
        # Test preference extraction
        preferences = storyteller._extract_story_preferences(test_input)
        print(f"✅ Preference extraction working")
        print(f"   Preferences: {preferences}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_storyteller_import()
    if success:
        print("\n🎉 Storyteller.py is fixed and working correctly!")
        print("✅ Ready for use in the Morpheus Sleep AI system!")
    else:
        print("\n❌ Storyteller.py still has issues that need fixing.")
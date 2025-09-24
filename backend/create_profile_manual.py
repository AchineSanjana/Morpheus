#!/usr/bin/env python3
"""
Manual profile creation script for existing users
"""

import requests
import json

# Your user ID from the error log
USER_ID = "11550470-afda-432b-bd5a-53763aa0bc63"

# API base URL
API_BASE = "http://localhost:8000"

def create_profile_manually():
    """
    Manually create a profile by calling the backend API
    Note: This bypasses auth checks for testing purposes
    """
    
    # First, let's try the new manual creation endpoint
    url = f"{API_BASE}/profile/{USER_ID}"
    
    print(f"Creating profile for user: {USER_ID}")
    print(f"Making POST request to: {url}")
    
    try:
        # For manual testing, we'll need to provide a token
        # Let's check if we can call it without auth first (may fail)
        response = requests.post(url, headers={"Authorization": "Bearer test"})
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Profile created successfully!")
            return response.json()
        else:
            print("❌ Failed to create profile via API")
            print("Let's try direct database insertion...")
            return create_profile_direct()
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server")
        print("Make sure the backend is running on port 8000")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def create_profile_direct():
    """
    Create profile directly in database (requires backend to be running)
    """
    # Import database functions
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from app.db import supabase
        
        # Create profile directly
        new_profile = {
            "id": USER_ID,
            "full_name": None,
            "username": "user_admin",  # Default username
            "avatar_url": None
        }
        
        print("Creating profile directly in database...")
        result = supabase.table("user_profile").insert(new_profile).execute()
        
        if result.data:
            print("✅ Profile created successfully in database!")
            print(f"Profile data: {result.data[0]}")
            return result.data[0]
        else:
            print("❌ Failed to create profile in database")
            return None
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

if __name__ == "__main__":
    profile = create_profile_manually()
    if profile:
        print("\n🎉 Success! Profile created:")
        print(json.dumps(profile, indent=2))
        print("\nNow try accessing your Account page in the app!")
    else:
        print("\n💡 Alternative: Try logging in and accessing the Account page")
        print("The auto-creation should work when you access /profile endpoint")
#!/usr/bin/env python3
"""
Simple manual profile creation script
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.db import supabase
    
    # Your user ID from the error log
    USER_ID = "11550470-afda-432b-bd5a-53763aa0bc63"
    
    print(f"Creating profile for user: {USER_ID}")
    
    # Check if profile already exists
    try:
        existing = supabase.table("user_profile").select("*").eq("id", USER_ID).single().execute()
        if existing.data:
            print("✅ Profile already exists!")
            print(f"Profile data: {existing.data}")
            exit(0)
    except:
        print("Profile doesn't exist, creating new one...")
    
    # First, let's see what columns exist
    try:
        # Try to get table schema by doing a simple select
        schema_check = supabase.table("user_profile").select("*").limit(1).execute()
        print(f"Existing table structure: {schema_check}")
    except Exception as schema_error:
        print(f"Schema check error: {schema_error}")
    
    # Create new profile with only basic fields that should exist
    new_profile = {
        "id": USER_ID,
        "username": "admin_user"  # Minimal profile
    }
    
    result = supabase.table("user_profile").insert(new_profile).execute()
    
    if result.data:
        print("✅ Profile created successfully!")
        print(f"Profile data: {result.data[0]}")
        print("\n🎉 Now try accessing your Account page in the app!")
    else:
        print("❌ Failed to create profile")
        print(f"Result: {result}")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure the backend environment is set up correctly")
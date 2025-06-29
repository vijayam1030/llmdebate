#!/usr/bin/env python3
"""
Test the API by importing and calling the endpoint directly
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_api_directly():
    """Test the API endpoint directly without starting a server"""
    print("🧪 Testing API endpoint directly...")
    
    try:
        # Import the FastAPI app
        from api.main import app, get_system_status
        print("✅ FastAPI app imported successfully!")
        
        # Call the status endpoint function directly
        print("\n📡 Calling get_system_status()...")
        status_response = await get_system_status()
        
        print(f"✅ Status response received!")
        print(f"Type: {type(status_response)}")
        print(f"Initialized: {status_response.initialized}")
        print(f"Models loaded: {status_response.models_loaded}")
        print(f"Config keys: {list(status_response.config.keys()) if hasattr(status_response.config, 'keys') else 'Not a dict'}")
        
        if hasattr(status_response.config, 'get') and status_response.config.get('error'):
            print(f"❌ Config error: {status_response.config['error']}")
        else:
            print("✅ No config errors detected!")
            
        # Test serialization to JSON (what FastAPI would do)
        try:
            json_data = status_response.model_dump()
            print(f"✅ JSON serialization successful!")
            print(f"JSON keys: {list(json_data.keys())}")
        except Exception as e:
            print(f"❌ JSON serialization error: {e}")
        
    except Exception as e:
        print(f"❌ Error during API test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_directly())

#!/usr/bin/env python3
"""
Test script for the FastAPI status endpoint
"""

import asyncio
import aiohttp
import json
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.main import app
from fastapi.testclient import TestClient

async def test_api():
    """Test the API endpoints directly"""
    print("🧪 Testing FastAPI endpoints...")
    
    # Create test client
    client = TestClient(app)
    
    print("\n1. Testing root endpoint...")
    try:
        response = client.get("/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n2. Testing status endpoint...")
    try:
        response = client.get("/api/status")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Initialized: {data.get('initialized', False)}")
            print(f"Models loaded: {data.get('models_loaded', [])}")
            print(f"Config keys: {list(data.get('config', {}).keys())}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n✅ API test complete!")

if __name__ == "__main__":
    asyncio.run(test_api())

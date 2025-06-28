#!/usr/bin/env python3
"""
Test script to verify direct Ollama API calls work
"""

import asyncio
import httpx
import json

async def test_ollama_direct():
    """Test direct Ollama API call"""
    print("Testing direct Ollama API call...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Test with tinyllama first (smallest model)
            payload = {
                "model": "tinyllama:1.1b",
                "prompt": "Human: What are renewable energy sources?\n\nAssistant: ",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                }
            }
            
            print(f"Calling Ollama API with payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=payload
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success! Response: {result.get('response', 'No response field')[:200]}...")
                return True
            else:
                print(f"Error: {response.status_code}")
                print(f"Response text: {response.text}")
                return False
                
    except Exception as e:
        print(f"Exception during test: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ollama_direct())
    if success:
        print("✅ Direct Ollama API test passed!")
    else:
        print("❌ Direct Ollama API test failed!")

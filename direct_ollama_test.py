#!/usr/bin/env python3
"""
Direct Ollama API test to bypass LangChain issues
"""

import asyncio
import httpx
import json

async def test_ollama_direct():
    """Test Ollama API directly"""
    print("🧪 Testing Ollama API directly...")
    
    # Test connection
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test version
            response = await client.get("http://localhost:11434/api/version")
            print(f"✅ Ollama version: {response.json()['version']}")
            
            # Test generate endpoint
            payload = {
                "model": "tinyllama:1.1b",
                "prompt": "What are the benefits of renewable energy? Answer in 2-3 sentences.",
                "stream": False
            }
            
            print("📡 Testing generate endpoint...")
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Generate endpoint works!")
                print(f"Response: {result.get('response', '')[:100]}...")
            else:
                print(f"❌ Generate endpoint failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama_direct())

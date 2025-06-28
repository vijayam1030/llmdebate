#!/usr/bin/env python3
"""
Simple Ollama connection test
"""

import httpx
import asyncio
import json

async def simple_test():
    """Simple test"""
    print("Testing connection...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test version
            response = await client.get("http://localhost:11434/api/version")
            print(f"Version: {response.json()}")
            
            # Simple generate test
            payload = {
                "model": "tinyllama:1.1b", 
                "prompt": "Hello",
                "stream": False,
                "options": {"num_predict": 10}
            }
            
            response = await client.post("http://localhost:11434/api/generate", json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Response: {result.get('response', '')}")
            else:
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(simple_test())

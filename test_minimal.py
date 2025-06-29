#!/usr/bin/env python3
"""
Minimal test to isolate the hanging issue
"""

import asyncio
import httpx
import sys

async def test_minimal_ollama():
    """Test minimal Ollama call"""
    print("Testing minimal Ollama call...")
    
    try:
        payload = {
            "model": "gemma2:2b",
            "prompt": "Say 'hi'",
            "stream": False,
            "options": {"num_predict": 3}
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://host.docker.internal:11434/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Response: {result.get('response', '').strip()}")
                return True
            else:
                print(f"Error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_minimal_ollama())
        print(f"Test result: {result}")
    except Exception as e:
        print(f"Fatal: {e}")
        sys.exit(1)

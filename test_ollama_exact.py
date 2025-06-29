import httpx
import asyncio
from config import Config

async def test():
    print(f"Testing connection to: {Config.OLLAMA_BASE_URL}")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{Config.OLLAMA_BASE_URL}/api/tags")
            print(f'Status: {response.status_code}')
            if response.status_code == 200:
                print("Connection successful!")
                data = response.json()
                print(f"Found {len(data.get('models', []))} models")
                return True
            else:
                print(f"Failed with status: {response.status_code}")
                return False
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

result = asyncio.run(test())
print(f'Result: {result}')

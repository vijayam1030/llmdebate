import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get('http://host.docker.internal:11434/api/tags')
        print('Status:', response.status_code)
        return response.status_code

result = asyncio.run(test())
print('Result:', result)

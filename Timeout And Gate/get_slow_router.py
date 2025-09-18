"""
Test for semaphores: the third call should return code 503 and header "Retry-After=1"
"""
import asyncio
import httpx

async def fetch(url):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.status_code, resp.text, resp.headers

async def main():
    url = "http://localhost:8000/slow_router"
    tasks = [fetch(url) for _ in range(3)]
    results = await asyncio.gather(*tasks)
    for i, (status, res, headers) in enumerate(results, 1):
        print(f"Response {i}: status={status}, body={res}, headers={headers}")

asyncio.run(main())
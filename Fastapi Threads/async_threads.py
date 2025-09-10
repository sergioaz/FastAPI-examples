import time
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
from concurrent.futures import ThreadPoolExecutor
import httpx
import uvicorn

app = FastAPI(
    title="Async testing",
    description="API for searching addresses using Elasticsearch with comparison capabilities",
    version="1.0.0",
)

async def long_running_cpu_task_async_generator():
    total = sum(i * i for i in range(10_000_000))
    return {"total": total}

async def long_running_cpu_task_async_cycle():
    total = 0
    for i in range (10_000_000):
        total += i*i

    return {"total": total}

async def long_running_cpu_task_async_sleep():
    total = 0
    for i in range(10_000_000):
        total += i * i
        if i % 100_000 == 0:
            await asyncio.sleep(0)  # Yield to event loop
    return {"total": total}

def long_running_cpu_task_sync():
    total = sum(i * i for i in range(10_000_000))
    return {"total": total}

@app.get("/generator")
async def generator():
    result = await long_running_cpu_task_async_generator()
    return {"data": result}

@app.get("/cycle")
async def cycle():
    result = await long_running_cpu_task_async_cycle()
    return {"data": result}

@app.get("/cycle_sleep")
async def cycle_sleep():
    result = await long_running_cpu_task_async_sleep()
    return {"data": result}


executor = ThreadPoolExecutor()
@app.get("/thread")
async def thread():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, long_running_cpu_task_sync)
    return {"result": result}


def main():
    import uvicorn
    uvicorn.run(
        "async_threads:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()

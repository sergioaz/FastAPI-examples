# FastAPI Threads - CPU-Bound Task Benchmark

This project demonstrates **4 different approaches** for handling long-running CPU-bound tasks in FastAPI applications. It benchmarks each approach to highlight the performance implications and best practices.

> ⚠️ **Important**: None of these 4 approaches should be used in production! This is purely educational to understand the differences.

## Overview

FastAPI is designed for I/O-bound operations (like database queries, API calls) using async/await. When dealing with CPU-bound tasks (heavy computations), different approaches have dramatically different performance characteristics, especially under concurrent load.

## The Problem

CPU-bound tasks in async applications can block the event loop, preventing other requests from being processed concurrently. This project demonstrates this issue and explores potential solutions.

## 5 Approaches Tested

### 1. **Async Generator** (`/generator`)
```python
async def long_running_cpu_task_async_generator():
    total = sum(i * i for i in range(10_000_000))
    return {"total": total}
```
- Uses Python's built-in `sum()` generator
- Still blocks the event loop despite being `async`
- **Performance**: Poor under concurrent load

### 2. **Async Cycle** (`/cycle`) 
```python
async def long_running_cpu_task_async_cycle():
    total = 0
    for i in range(10_000_000):
        total += i*i
    return {"total": total}
```
- Manual loop with accumulation
- Completely blocks the event loop
- **Performance**: Worst under concurrent load

### 3. **Async Cycle with Sleep** (`/cycle_sleep`)
```python
async def long_running_cpu_task_async_sleep():
    total = 0
    for i in range(10_000_000):
        total += i * i
        if i % 100_000 == 0:
            await asyncio.sleep(0)  # Yield to event loop
    return {"total": total}
```
- Periodically yields control back to the event loop
- Allows other requests to be processed
- **Performance**: Better concurrency, but slower overall

### 4. **Thread Pool Executor** (`/thread`)
```python
def long_running_cpu_task_sync():  # Note: sync function
    total = sum(i * i for i in range(10_000_000))
    return {"total": total}

@app.get("/thread")
async def thread():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, long_running_cpu_task_sync)
    return {"result": result}
```
- Offloads CPU work to a separate thread
- Keeps the main event loop free
- **Performance**: Best for concurrent requests


### 5. **FastAPI Background Tasks** (`/background`)
```python
def long_running_cpu_task_sync():  # Note: sync function
    total = sum(i * i for i in range(10_000_000))
    return {"total": total}

@app.get("/background")
async def register(background_tasks: BackgroundTasks):
    background_tasks.add_task(long_running_cpu_task_sync)
    return {"message": "long running task queued"}
```
- Works only in "fire-and-forget" mode, no direct way to get results or status
- Keeps the main event loop free immediately
- **Performance**: Best for concurrent requests where you don't need results ( send email, for example)

##

## Installation & Usage

### Prerequisites
- Python 3.7+
- Virtual environment activated

### Setup
```powershell
# Navigate to project directory
cd "C:\Learn\FastAPI-Projects\Fastapi Threads"

# Install dependencies (if not already installed)
..\..\.venv\Scripts\pip.exe install fastapi uvicorn httpx

# Start the FastAPI server
..\..\. venv\Scripts\python.exe async_threads.py
```

The server will start at `http://localhost:8000`

### API Endpoints
- `GET /generator` - Async with built-in generator
- `GET /cycle` - Async with manual loop  
- `GET /cycle_sleep` - Async with periodic yielding
- `GET /thread` - Thread pool executor approach
- `GET /docs` - Interactive API documentation

## Running the Benchmark

### Start the Server
```powershell
..\..\. venv\Scripts\python.exe async_threads.py
```

### Run Benchmark (in separate terminal)
```powershell
..\..\. venv\Scripts\python.exe benchmark.py
```

The benchmark will:
1. Send 20 concurrent requests to each endpoint
2. Measure total time for each batch
3. Display performance comparison

### Expected Results
```
--- Starting benchmark ---

Running 20 requests to /thread...
Batch of 20 requests to /thread took: 22.0327 seconds
--------------------
Running 20 requests to /generator...
Batch of 20 requests to /generator took: 11.2745 seconds
--------------------
Running 20 requests to /cycle...
Batch of 20 requests to /cycle took: 8.9993 seconds
--------------------
Running 20 requests to /cycle_sleep...
Batch of 20 requests to /cycle_sleep took: 13.4933 seconds

Running 20 requests to /background...
Batch of 20 requests to /background took: 0.4740 seconds
```

## Performance Analysis

| Approach | Concurrency | Event Loop | Performance | Use Case |
|----------|-------------|------------|-------------|----------|
| **Thread Pool** | ✅ Excellent | ✅ Non-blocking | ⭐⭐⭐⭐⭐ Best | Recommended for CPU tasks |
| **Generator** | ❌ Poor | ❌ Blocking | ⭐⭐ Poor | Educational only |
| **Manual Cycle** | ❌ Terrible | ❌ Blocking | ⭐ Worst | Educational only |
| **Cycle + Sleep** | ✅ Good | ⚠️ Partially blocking | ⭐⭐⭐ Moderate | Educational only |

## Key Learnings

### ❌ What NOT to do:
1. **Don't use `async` for CPU-bound tasks** - It doesn't make them concurrent
2. **Don't use ThreadPoolExecutor** for CPU-bound tasks - does not help much
3. **Don't block the event loop** - Other requests will queue up
4. **Don't use `asyncio.sleep(0)`** as a solution - It's a hack, not a fix


### ✅ What TO do:
1. **Keep async functions for I/O operations** 
2. **Consider multiprocessing** for truly parallel CPU work
3. **Profile your application** under realistic load

## Production Alternatives

For real-world applications, consider:

### 1. **Background Task Queues**
```python
# Use Celery, RQ, or similar
from celery import Celery

@app.post("/heavy-task")
async def queue_heavy_task():
    task_id = heavy_computation.delay()
    return {"task_id": task_id}
```

### 2. **Microservices Architecture**
- Separate CPU-intensive operations into dedicated services
- Use message queues for communication
- Scale independently

### 3. **Caching Results**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(input_data):
    # Heavy computation
    return result
```

## Files Description

- `async_threads.py` - Main FastAPI application with 4 endpoints
- `benchmark.py` - Performance testing script
- `__init__.py` - Package marker
- `README.md` - This documentation

## Dependencies

- **FastAPI** - Web framework
- **uvicorn** - ASGI server
- **httpx** - HTTP client for benchmarking
- **asyncio** - Async programming support
- **concurrent.futures** - Thread pool executor

## Related Projects

In this repository, also check out:
- **Celery in FastAPI** - Proper background task handling
- **Fastapi Background Tasks** - FastAPI's built-in background tasks
- **Redis in FastAPI** - Caching strategies

## Warning

⚠️ **This code is for educational purposes only!** 

The approaches demonstrated here (especially `/generator`, `/cycle`, and `/cycle_sleep`) will severely impact your application's performance in production. Always use proper background task queues or microservices for CPU-intensive operations.

## Contributing

This is a demonstration project. If you find improvements to the benchmarking methodology or additional approaches to test, contributions are welcome!

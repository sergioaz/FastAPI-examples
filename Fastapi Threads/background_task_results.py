from fastapi import FastAPI, BackgroundTasks
from typing import Dict, Any, Optional
import uuid
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

app = FastAPI()

# In-memory storage for task results (use Redis/database in production)
task_results: Dict[str, Dict[str, Any]] = {}

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"

def long_running_cpu_task_sync():
    """Your original CPU-intensive task"""
    total = sum(i * i for i in range(10_000_000))
    return {"total": total}

def background_task_with_result(task_id: str, func, *args, **kwargs):
    """Wrapper to store task results"""
    try:
        task_results[task_id]["status"] = TaskStatus.RUNNING
        result = func(*args, **kwargs)
        task_results[task_id].update({
            "status": TaskStatus.COMPLETED,
            "result": result,
            "completed_at": time.time()
        })
    except Exception as e:
        task_results[task_id].update({
            "status": TaskStatus.FAILED,
            "error": str(e),
            "failed_at": time.time()
        })

# Approach 1: Task ID with Status Polling
@app.post("/background-with-id")
async def start_background_task(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    task_results[task_id] = {
        "status": TaskStatus.PENDING,
        "created_at": time.time()
    }
    
    background_tasks.add_task(
        background_task_with_result, 
        task_id, 
        long_running_cpu_task_sync
    )
    
    return {
        "message": "Task started",
        "task_id": task_id,
        "status_url": f"/task-status/{task_id}"
    }

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in task_results:
        return {"error": "Task not found"}, 404
    
    return task_results[task_id]

# Approach 2: Using ThreadPoolExecutor (returns result immediately)
executor = ThreadPoolExecutor()

@app.post("/sync-with-thread")
async def run_in_thread():
    """Run sync task in thread pool and return result"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, long_running_cpu_task_sync)
    return {"result": result, "message": "Task completed"}

# Approach 3: Converting to async (if possible)
async def long_running_task_async():
    """Async version with periodic yielding"""
    total = 0
    for i in range(10_000_000):
        total += i * i
        if i % 100_000 == 0:
            await asyncio.sleep(0)  # Yield control to event loop
    return {"total": total}

@app.post("/async-task")
async def run_async_task():
    """Run as async task (blocks until complete but yields control)"""
    result = await long_running_task_async()
    return {"result": result, "message": "Async task completed"}

# Approach 4: WebSocket for real-time updates (advanced)
from fastapi import WebSocket

@app.websocket("/ws/{task_id}")
async def websocket_task_updates(websocket: WebSocket, task_id: str):
    await websocket.accept()
    
    # Start the background task
    background_tasks = BackgroundTasks()
    if task_id not in task_results:
        task_results[task_id] = {"status": TaskStatus.PENDING, "created_at": time.time()}
        background_tasks.add_task(background_task_with_result, task_id, long_running_cpu_task_sync)
    
    # Poll and send updates
    while True:
        if task_id in task_results:
            await websocket.send_json(task_results[task_id])
            if task_results[task_id]["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                break
        await asyncio.sleep(1)  # Check every second
    
    await websocket.close()

# Utility endpoints
@app.get("/tasks")
async def list_all_tasks():
    """Get status of all tasks"""
    return task_results

@app.delete("/task/{task_id}")
async def clear_task_result(task_id: str):
    """Clear a specific task result"""
    if task_id in task_results:
        del task_results[task_id]
        return {"message": "Task result cleared"}
    return {"error": "Task not found"}, 404

def main():
    import uvicorn
    uvicorn.run(
        "background_task_results:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()

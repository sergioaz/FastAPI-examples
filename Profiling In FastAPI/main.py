import time
from fastapi import FastAPI, Request, APIRouter
"""
Examples of light-weight profiling in FastAPI
Main Point: to take samples
"""

app = FastAPI(
    title="Address Search API",
    description="API for searching addresses using Elasticsearch with comparison capabilities",
    version="1.0.0",
    #lifespan=lifespan
)

router = APIRouter()

# version 1: middleware and print
@app.middleware("http")
async def add_profiling(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000
    if hash(request.url.path) % 100 == 0:  # Sample ~1% of requests
        print(f"Profiling: {request.url.path} took {process_time:.2f} ms")
    return response

@router.get("/profile")
async def get_profile():
    return {"profile": "Profile 1"}

# version 2: CPU & Memory Profiling With Pyroscope - Linux only!
"""
import pyroscope

pyroscope.configure(
    application_name="fastapi-app",
    server_address="http://pyroscope:4040",
    enable_logging=False
)
"""

def main():
    import uvicorn
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
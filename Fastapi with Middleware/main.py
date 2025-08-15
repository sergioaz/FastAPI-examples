from fastapi import FastAPI,  Body, Request
from middleware import MyMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
my_middleware = MyMiddleware(some_attribute="some_attribute_here_if_needed")
app.add_middleware(BaseHTTPMiddleware, dispatch=my_middleware)


@app.post("/")
async def root(json_body: dict = Body(...)):
    time.sleep(6) # Simulating some heavy processing
    return {"message": "Hello World"}


#Request Logging Middleware
#Logging incoming requests with method, path, and headers is a lifesaver when debugging issues or tracing anomalies.
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming {request.method} {request.url.path}")
    response = await call_next(request)
    return response

#3. Request ID Injection
#Unique request IDs improve log tracing across distributed systems, especially in microservices.

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


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
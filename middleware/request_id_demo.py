from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from uuid import uuid4


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id  # store it in request context

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id  # propagate to response
        return response


from fastapi import FastAPI

app = FastAPI()
app.add_middleware(RequestIDMiddleware)

from fastapi import Request


@app.get("/debug")
async def debug(request: Request):
    print(f"Request ID: {request.state.request_id}")
    return {"request_id": request.state.request_id}
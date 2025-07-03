from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 🔹 Before request
        print(f"Request URL: {request.url}")

        # Call the next middleware or route
        response = await call_next(request)

        # 🔹 After response
        response.headers["X-Custom-Header"] = "MyValue"
        return response


# Add middleware to app
app.add_middleware(CustomHeaderMiddleware)


@app.get("/")
async def read_main():
    return {"message": "Hello World"}
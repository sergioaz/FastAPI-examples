"""
Rate limiting for FastAPI
"""
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Version 1: with slowapi, by user IP
app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return _rate_limit_exceeded_handler(request, exc)


@app.get("/items")
@limiter.limit("5/minute")
async def read_items(request: Request):
    return {"msg": "Success"}

# version 2: using headers

def get_user_key(request: Request):
    return request.headers.get("X-API-Key", "anonymous")

limiter2 = Limiter(key_func=get_user_key)

@app.get("/items2")
@limiter.limit("10/minute")
async def read_items(request: Request):
    return {"msg": "Success"}


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
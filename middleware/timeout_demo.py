from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import asyncio

app = FastAPI()


@app.middleware("http")
async def timeout_middleware(request, call_next):
    try:
        return await asyncio.wait_for(call_next(request), timeout=5.0)
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"message": "Request timed out"})


@app.get("/timeout")
async def read_items(request: Request):
    await asyncio.sleep(10)
    return {"msg": "Success"}

def main():
    import uvicorn
    uvicorn.run(
        "timeout_demo:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
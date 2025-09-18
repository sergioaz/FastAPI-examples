"""
Deadlines everywhere + admission control
Goal: bound the worst-case and shed early instead of drowning.
"""
import asyncio
from fastapi import HTTPException, FastAPI, Response
import os

app = FastAPI()

async def slow_ext_call(params):
    await asyncio.sleep (0.005)
    return {"sleeped": 0.5}

"""
Put per-request budgets around downstream hops and business logic
"""
@app.get("/slow_router")
async def slow_router():
    try:
        async with asyncio.timeout(0.040):  # 40 ms budget
            return await slow_ext_call(params=None)
    except TimeoutError:
        raise HTTPException(status_code=503, detail="timeout")



"""
Add a global gate with a semaphore so bursts don’t starve everyone:
"""
#gate = asyncio.Semaphore(1500)  # match --limit-concurrency
gate = asyncio.Semaphore(2)  # match --limit-concurrency

@app.middleware("http")
async def gatekeeper(req, call_next):
    if gate._value > 0:
        acquired = await gate.acquire()
        try:
            response = await call_next(req)
            # test with 2 semaphores and sleep (1)
            await asyncio.sleep(1)
            return response
        finally:
            gate.release()
    else:
        return Response(content="", status_code=503, headers={"Retry-After": "1"})

def main():
    import uvicorn
    config = uvicorn.Config(
        "main:app",
        # loop="uvloop",  ## uvloop does not support Windows as of now
        # http="httptools",
        # workers=2,
        backlog=2048,
        limit_concurrency=1500,
        timeout_keep_alive=5,
        host="localhost",
        port=8000,
        reload=False,
        log_level="info"
    )
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    main()
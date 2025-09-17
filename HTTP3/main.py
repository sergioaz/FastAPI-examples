"""
Put HTTP/3 (QUIC) at the edge; keep FastAPI on warm keep-alives
Goal: win back RTTs and avoid head-of-line blocking without complicating your app tier.

Terminate HTTP/3 at an edge proxy/CDN close to users. Forward to FastAPI over HTTP/1.1 or HTTP/2 with long-lived keep-alive.
Use 0-RTT only for idempotent requests. Enforce it in app code:
"""
from fastapi import FastAPI, Request, Response, status

app = FastAPI()

@app.middleware("http")
async def reject_early_mutations(req: Request, call_next):
    early = req.headers.get("early-data") == "1" or req.headers.get("x-0rtt") == "1"
    if early and req.method not in ("GET", "HEAD"):
        return Response(status_code=status.HTTP_425_TOO_EARLY, headers={"Retry-After": "0"})
    return await call_next(req)
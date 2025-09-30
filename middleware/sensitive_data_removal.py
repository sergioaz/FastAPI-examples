"""
Example how to remove sensitive data from saving in logs
"""
# middleware_io.py
import json, logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
logger = logging.getLogger("io")

REDACT_KEYS = {"password", "token", "authorization", "secret"}

def _redact(obj):
    if isinstance(obj, dict):
        return {k: ("***" if k.lower() in REDACT_KEYS else _redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj

MAX_LEN = 2_000  # bytes

class RequestResponseLogger(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        body = (await request.body())[:MAX_LEN]
        try:
            parsed = _redact(json.loads(body.decode() or "{}"))
        except Exception:
            parsed = "<non-json>"
        logger.info("request", extra={"_extra": {
            "cid": getattr(request.state, "correlation_id", None),
            "method": request.method, "path": request.url.path, "body": parsed
        }})
        response = await call_next(request)
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        response.body_iterator = iter([response_body])  # reassign body
        preview = response_body[:MAX_LEN].decode(errors="ignore")
        logger.info("response", extra={"_extra": {
            "cid": getattr(request.state, "correlation_id", None),
            "status": response.status_code, "body": preview[:500]  # shallow peek
        }})
        return response
'''
15. Helmet Middleware(Security Headers)
AAdd essential HTTP headers to secure your FastAPI app against common vulnerabilities like XSS, clickjacking, and MIME sniffing.
In the Node.js world, Helmet is a middleware that automatically sets secure headers like:

X - Content - Type - Options
X - Frame - Options
Strict - Transport - Security
Content - Security - Policy
Referrer - Policy
'''

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class HelmetMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=()"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self'; "
            "font-src 'self'; "
        )

        return response


from fastapi import FastAPI

app = FastAPI()
app.add_middleware(HelmetMiddleware)

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>Helmet Middleware Demo</h1><p>This is a secure FastAPI app.</p>"

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

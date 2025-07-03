Middlewares: 
https://medium.com/the-pythonworld/15-useful-middlewares-for-fastapi-that-you-should-know-about-8c2d67ea0d86

1. ----- Intercept requests / returns  ----------
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
	
2. ------ CORS - enabler (CORS (Cross-Origin Resource Sharing) is a mechanism that allows your frontend JavaScript app (on one domain) to securely interact with your FastAPI backend (on another domain))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allowed origins (can be specific URLs or wildcards)
origins = [
    "http://localhost",
    "http://localhost:3000",  # your frontend dev server
    "https://yourfrontenddomain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,             # allowed frontend origins
    allow_credentials=True,            # allow cookies, headers, sessions
    allow_methods=["*"],               # allow all HTTP methods
    allow_headers=["*"],               # allow all headers
)	
	
3. ---------- GZipMiddleware ---------

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()

# Add GZip middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

4. ========== TrustedHostMiddleware-----------
Use this middleware to protect your FastAPI app against Host header attacks, like DNS rebinding.
It allows you to whitelist the domains your app should respond to. If a request comes in with an unknown Host header — it gets rejected with a 400 Bad Request.

from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "example.com",           # main domain
        "*.example.com",         # all subdomains
        "localhost",             # for local dev
        "127.0.0.1"              # also valid for dev
    ]
)

5. ------------ Request Logging Middleware -----------
Logs every incoming HTTP request and outgoing response, helping you trace errors, analyze traffic, and monitor system behavior in real time.

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log incoming request
        logger.info(f"➡️ {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        process_time = round((time.time() - start_time) * 1000, 2)
        
        # Log response status and duration
        logger.info(f"⬅️ {request.method} {request.url.path} - {response.status_code} ({process_time} ms)")
        
        return response

# Add to app
app.add_middleware(LoggingMiddleware)

@app.get("/hello")
async def hello():
    return {"message": "Hello, world!"}
	
6. ============ SlowAPI (Rate Limiting) -------------
Use SlowAPI to prevent abuse, brute-force attacks, and API overuse by limiting how often a client (usually by IP) can hit your endpoints.	

uv pip install slowapi

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI()

# Initialize Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Add exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/limited")
@limiter.limit("5/minute")
async def limited_endpoint(request: Request):
    return {"message": "This is a rate-limited endpoint"}
	
curl http://localhost:8000/limited

6th time: 
429 Too Many Requests

7. ------------ Session Middleware (Starlette) -----------
SessionMiddleware allows you to store user-specific data on the server (like login state, user preferences, or cart items) while tracking users via signed cookies.	

from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key",  # 🔐 used for signing the cookie
    session_cookie="myapp_session", # optional: custom cookie name
    max_age=86400                   # optional: cookie expiration in seconds (1 day)
)

@app.get("/set-session")
async def set_session(request: Request):
    request.session["username"] = "aashish"
    return {"message": "Session set"}

@app.get("/get-session")
async def get_session(request: Request):
    username = request.session.get("username", "Guest")
    return {"username": username}
	
======== Example Use Case: Login System ========
@app.post("/login")
async def login(request: Request):
    # Assume user is authenticated
    request.session["user_id"] = "12345"
    return {"message": "Logged in"}

@app.get("/me")
async def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return {"message": "Not logged in"}
    return {"user_id": user_id}	


8. =========== CORSMiddleware + Custom Preflight Caching============
Improve frontend performance by caching CORS preflight responses using custom headers — reducing unnecessary network calls.

Whenever a browser makes a cross-origin request with:

A custom header (e.g., Authorization)
A method like PUT, PATCH, or DELETE
Cookies or credentials
…it first sends a preflight request:

OPTIONS /endpoint
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Authorization
This checks if the actual request is allowed, based on your CORS rules.

The Fix: Custom Preflight Caching
Tell the browser:
“Hey, this preflight result is valid for a while — no need to ask again.”

We do this by setting the Access-Control-Max-Age header.

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

# Step 1: Add default CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Step 2: Create a custom middleware to set Access-Control-Max-Age
class PreflightCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            response = await call_next(request)
            # 🧠 Tell the browser to cache the preflight response for 10 minutes
            response.headers["Access-Control-Max-Age"] = "600"
            return response
        return await call_next(request)

app.add_middleware(PreflightCacheMiddleware)

Test With curl
curl -X OPTIONS http://localhost:8000/api \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization"
You should see:

Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Max-Age: 600

9. ------------- Sentry Middleware (Error Monitoring) ------------
Catch exceptions, monitor performance, and get notified instantly when your FastAPI app crashes — using Sentry.

https://home-office-inc.sentry.io/

uv pip install --upgrade sentry-sdk

from fastapi import FastAPI
import sentry_sdk

sentry_sdk.init(
    dsn="https://4e1dcbf812bb2156351a04054f3bb0bb@o4509600462667776.ingest.us.sentry.io/4509600464961536",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

app = FastAPI()

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0
	
	
10. ---------- Prometheus Middleware (Metrics) ----------
Expose rich metrics from your FastAPI app — like request counts, error rates, and latency — using Prometheus and visualize them using tools like Grafana.
How many requests is my app serving per second?
Which endpoints are slow?
How often are errors happening?
What’s the average latency per route?
All of this makes it easier to:

Diagnose issues in real-time
Trigger alerts on anomalies
Monitor performance trends
Ensure SLAs are met

uv pip install prometheus-fastapi-instrumentator

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Create instrumentator instance
instrumentator = Instrumentator().instrument(app).expose(app)

@app.get("/ping")
async def ping():
    return {"message": "pong"}

That’s it! Your metrics are now being tracked and exposed at:

GET /metrics

# customize:
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    env_var_name="ENABLE_METRICS",
)

instrumentator.instrument(app).expose(app, include_in_schema=False)	

---
11. ---------- Cache Middleware ----------
Use caching to reduce redundant processing and database queries — speeding up your FastAPI endpoints dramatically.

uv pip install fastapi-cache2[redis]

from fastapi import FastAPI
from fastapi_cache2 import FastAPICache
from fastapi_cache2.backends.redis import RedisBackend
import redis.asyncio as redis

app = FastAPI()

@app.on_event("startup")
async def startup():
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    FastAPICache.init(RedisBackend(r), prefix="fastapi-cache")

# 12. SQLAlchemy Session Middleware
Automatically create and teardown a SQLAlchemy session per request — the cleanest way to manage database access in FastAPI.

pip install sqlalchemy
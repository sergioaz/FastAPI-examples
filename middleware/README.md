# FastAPI Middleware Collection

A comprehensive collection of middleware examples for FastAPI applications, demonstrating various patterns to extend and enhance your API functionality.

## Overview

Middleware in FastAPI allows you to process requests and responses before they reach your route handlers or after they leave them. This collection showcases practical middleware implementations for common use cases such as:

- Security enhancements
- Performance optimization
- Logging and monitoring
- Authentication and authorization
- Request/response manipulation

## Middleware Examples

### 1. Base Middleware Pattern

[`fastapi_base_middleware_scratch_107.py`](./fastapi_base_middleware_scratch_107.py) - The fundamental pattern for creating custom middleware in FastAPI.

```python
class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Before request processing
        print(f"Request URL: {request.url}")
        
        # Call the next middleware or route handler
        response = await call_next(request)
        
        # After response processing
        response.headers["X-Custom-Header"] = "MyValue"
        return response
```
	
### 2. CORS Middleware

Enables secure cross-origin requests from your frontend (on one domain) to your FastAPI backend (on another domain).

```python
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
```

### 3. GZip Compression Middleware

Automatically compresses responses to reduce bandwidth and improve loading times for your API responses.

```python
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()

# Add GZip middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Only compress responses > 1KB
```

### 4. Trusted Host Middleware

Protects your FastAPI app against Host header attacks (like DNS rebinding) by whitelisting allowed domains. Rejects requests with unknown Host headers with 400 Bad Request.

```python
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
```

### 5. Request Logging Middleware
Logs every incoming HTTP request and outgoing response, helping you trace errors, analyze traffic, and monitor system behavior in real time.

```python
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
```

## 6. SlowAPI (Rate Limiting) 
Use SlowAPI to prevent abuse, brute-force attacks, and API overuse by limiting how often a client (usually by IP) can hit your endpoints.	

```python
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
```
curl http://localhost:8000/limited

6th time: 
429 Too Many Requests
```json
{
    "detail": "Rate limit exceeded. Limit: 5/minute"
}
```

## 7. Session Middleware (Starlette) 
SessionMiddleware allows you to store user-specific data on the server (like login state, user preferences, or cart items) while tracking users via signed cookies.	

```uv pip install starlette```
```python
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
```

======== Example Use Case: Login System ========
```python
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
```

## 8. CORSMiddleware + Custom Preflight Caching
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
```python

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
```

Test With curl
curl -X OPTIONS http://localhost:8000/api \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization"
You should see:

Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Max-Age: 600

## 9. Sentry Middleware (Error Monitoring) 
Catch exceptions, monitor performance, and get notified instantly when your FastAPI app crashes — using Sentry.

https://home-office-inc.sentry.io/

```
uv pip install --upgrade sentry-sdk
```

```python
from fastapi import FastAPI
import sentry_sdk

sentry_sdk.init(
    dsn="https://xxxxxx.ingest.us.sentry.io/xxxxxx",  # Replace with your Sentry DSN
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

app = FastAPI()

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0
```
	
## 10. Prometheus Middleware (Metrics)
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

```bash
uv pip install prometheus-fastapi-instrumentator
```

```python
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Create instrumentator instance
instrumentator = Instrumentator().instrument(app).expose(app)

@app.get("/ping")
async def ping():
    return {"message": "pong"}
```

That’s it! Your metrics are now being tracked and exposed at:

GET /metrics

Customize:
```python
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    env_var_name="ENABLE_METRICS",
)

instrumentator.instrument(app).expose(app, include_in_schema=False)	
```


## 11. Cache Middleware
Use caching to reduce redundant processing and database queries — speeding up your FastAPI endpoints dramatically.

```bash
uv pip install fastapi-cache2[redis]
```

```python
from fastapi import FastAPI
from fastapi_cache2 import FastAPICache
from fastapi_cache2.backends.redis import RedisBackend
import redis.asyncio as redis

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize FastAPI Cache with Redis backend
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    FastAPICache.init(RedisBackend(r), prefix="fastapi-cache")

    yield
```

### 12. SQLAlchemy Session Middleware

Automatically create and teardown a SQLAlchemy session per request — the cleanest way to manage database access in FastAPI.

```bash
pip install sqlalchemy psycopg2-binary  # For PostgreSQL
# or
pip install sqlalchemy pymysql         # For MySQL
```

```python
from fastapi import FastAPI, Request, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from starlette.middleware.base import BaseHTTPMiddleware

# Database setup
DATABASE_URL = "postgresql://user:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

app = FastAPI()

# Session Middleware
class DatabaseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.db = SessionLocal()
        try:
            response = await call_next(request)
        finally:
            request.state.db.close()
        return response

app.add_middleware(DatabaseMiddleware)

# Dependency to get database session
def get_db(request: Request) -> Session:
    return request.state.db

# Route using the session
@app.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    return user

@app.post("/users/")
async def create_user(name: str, email: str, db: Session = Depends(get_db)):
    user = User(name=name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

**Alternative: Using FastAPI's built-in dependency system (recommended):**
```python
from contextlib import contextmanager

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Or with async context manager
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_async_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
uv pip install sqlalchemy


## 13. Timeout Middleware
Prevent long-running requests from hanging your FastAPI application by enforcing timeouts on request processing.
```python
import asyncio
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
```


## 🚩 Feature Flag Demo Application

[`feature_flag_demo.py`](./feature_flag_demo.py) - A comprehensive FastAPI application demonstrating advanced feature flag patterns and middleware integration.

### Overview

The Feature Flag Demo showcases a production-ready feature flag system with multiple flag types, A/B testing capabilities, and comprehensive management APIs. This demo illustrates how feature flags can be used to:

- 🔄 **Gradual Rollouts**: Release features to a percentage of users
- 👥 **User Targeting**: Enable features for specific user groups
- 🧪 **A/B Testing**: Run controlled experiments with multiple variants
- 🚨 **Emergency Controls**: Instantly disable problematic features
- 📊 **Analytics**: Track feature usage and performance metrics

### Feature Flag Types Supported

1. **Simple Flags** - Basic on/off toggles
2. **Percentage Rollouts** - Gradual feature releases (0-100%)
3. **User-specific Flags** - Allowlists and blocklists
4. **A/B Testing** - Multi-variant experiments with control groups
5. **Emergency Disable** - Instant kill switches for any flag

### Key Components

#### 1. FeatureFlagService Class
```python
class FeatureFlagService:
    def is_enabled(self, flag_name: str, user_id: Optional[str] = None, context: Optional[Dict] = None) -> bool:
        # Intelligent flag evaluation with user hashing
        # Support for percentage rollouts and A/B testing
        # Built-in analytics and usage tracking
```

#### 2. FeatureFlagMiddleware
```python
class FeatureFlagMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Inject feature flag service into request state
        # Add user context from headers
        # Include experiment group info in response headers
```

#### 3. Comprehensive API Endpoints

**Admin Endpoints (Feature Flag Management):**
- `POST /admin/feature-flags` - Create/update feature flags
- `GET /admin/feature-flags` - List all feature flags
- `GET /admin/feature-flags/{name}` - Get specific flag configuration
- `DELETE /admin/feature-flags/{name}` - Remove feature flags
- `POST /admin/feature-flags/{name}/emergency-disable` - Emergency kill switch
- `GET /admin/feature-flags/{name}/stats` - Usage statistics

**Demo Endpoints (Feature Testing):**
- `GET /demo/simple-feature` - Simple on/off flag demo
- `GET /demo/percentage-feature` - Percentage rollout demo
- `GET /demo/user-feature` - User-specific targeting demo
- `GET /demo/ab-test-feature` - A/B testing with variants
- `POST /demo/payment` - Payment processor switching demo
- `GET /demo/recommendations` - ML vs rule-based recommendations

### Usage Examples

#### 1. Creating a Simple Feature Flag
```bash
curl -X POST "http://localhost:8000/admin/feature-flags" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new_dashboard",
    "enabled": true,
    "flag_type": "simple",
    "description": "New dashboard UI"
  }'
```

#### 2. Percentage-based Rollout
```bash
curl -X POST "http://localhost:8000/admin/feature-flags" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "beta_feature",
    "enabled": true,
    "flag_type": "percentage",
    "percentage": 25,
    "description": "Beta feature for 25% of users"
  }'
```

#### 3. A/B Testing Setup
```bash
curl -X POST "http://localhost:8000/admin/feature-flags" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "checkout_experiment",
    "enabled": true,
    "flag_type": "ab_test",
    "experiment_groups": {
      "control": 33,
      "variant_a": 33,
      "variant_b": 34
    },
    "description": "Checkout flow A/B test"
  }'
```

#### 4. Testing with User Headers
```bash
# Test percentage rollout
curl -H "X-User-ID: user123" "http://localhost:8000/demo/percentage-feature"

# Test A/B experiment
curl -H "X-User-ID: test_user" "http://localhost:8000/demo/ab-test-feature"
```

### Advanced Features

#### 1. Consistent User Hashing
The system uses MD5 hashing to ensure users consistently see the same feature state across sessions:
```python
hash_input = f"{flag_name}:{user_id}"
user_hash = int(hashlib.md5(hash_input.encode()).hexdigest(), 16) % 100
return user_hash < percentage
```

#### 2. Real-time Analytics
Built-in usage tracking for all feature flags:
```python
stats = {
    "total_checks": 1547,
    "enabled_count": 387,
    "disabled_count": 1160,
    "last_checked": "2024-01-15T14:30:00Z"
}
```

#### 3. Emergency Controls
Instant kill switches for problematic features:
```python
# Emergency disable any feature
feature_service.emergency_disable("problematic_feature")
```

### Testing the Demo

1. **Start the application:**
```bash
uvicorn feature_flag_demo:app --host 0.0.0.0 --port 8000 --reload
```

2. **Use the HTTP test file:**
```bash
# Use feature_flag_demo.http for comprehensive API testing
# Contains 25+ test scenarios covering all feature types
```

3. **Monitor logs:**
```bash
# Watch real-time feature flag evaluations
tail -f application.log
```

### Production Considerations

- **Storage**: Replace in-memory storage with Redis/Database
- **Authentication**: Add proper admin API authentication
- **Caching**: Implement flag configuration caching
- **Monitoring**: Integrate with monitoring systems (Prometheus/Grafana)
- **Audit Logs**: Track all flag configuration changes
- **Rollback**: Implement flag change history and rollback capabilities

### HTTP Test File

The [`feature_flag_demo.http`](./feature_flag_demo.http) file contains comprehensive test scenarios:

- ✅ **26 Different Test Cases**
- 🎯 **All Feature Flag Types Covered**
- 👤 **Multiple User Scenarios**
- 🚨 **Edge Case Testing**
- 📊 **Statistics and Analytics Testing**
- 🔧 **Admin Management Operations**

### Demo Highlights

- **Payment Processor Switching**: Safely rollout new payment systems
- **ML vs Rule-based Recommendations**: A/B test recommendation engines
- **User-specific Features**: VIP features for premium users
- **Emergency Disable**: Instant rollback capabilities
- **Comprehensive Analytics**: Track feature performance and adoption

This feature flag system demonstrates enterprise-grade patterns suitable for production applications requiring controlled feature rollouts, A/B testing, and risk mitigation.

---

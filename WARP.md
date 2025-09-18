# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Quick-Start Commands (PowerShell)

### Environment Setup
```powershell
# Activate virtual environment (required for all development)
.\.venv\Scripts\Activate.ps1

# Install/update dependencies
.\.venv\Scripts\pip.exe install -e .

# Install dev dependencies
.\.venv\Scripts\pip.exe install -e ".[dev]"
```

### Running Applications
```powershell
# Standard way to run any FastAPI app (replace PROJECT_NAME)
.\.venv\Scripts\uvicorn.exe "PROJECT_NAME.main:app" --reload --host 0.0.0.0 --port 8000

# Examples for specific projects:
.\.venv\Scripts\uvicorn.exe "CRUD Operation With SQLAlchemy.main:app" --reload
.\.venv\Scripts\uvicorn.exe "JWT Authentication In FastAPI.main:app" --reload
.\.venv\Scripts\uvicorn.exe "FastAPI With MongoDB.main:app" --reload

# For projects with custom entry points
.\.venv\Scripts\python.exe ".\JWT Authentication In FastAPI\main.py"
```

### Testing
```powershell
# Run all tests
.\.venv\Scripts\pytest.exe

# Run tests for specific project
.\.venv\Scripts\pytest.exe ".\Pytest Testing With FastAPI\"

# Run tests with coverage
.\.venv\Scripts\pytest.exe --cov=. --cov-report=html

# Run single test file
.\.venv\Scripts\pytest.exe ".\Pytest Testing With FastAPI\test_api.py" -v
```

### Development Tools
```powershell
# Code formatting
.\.venv\Scripts\black.exe .

# Linting
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe check --fix .

# Type checking
.\.venv\Scripts\mypy.exe .
```

## Repository Structure & High-Level Architecture

This repository contains **35+ independent FastAPI demonstration projects**, each showcasing specific patterns and use cases:

### Project Categories
- **Authentication & Authorization**: JWT Authentication, Role Base Authentication, Resource Access Management
- **Database Integration**: CRUD Operation With SQLAlchemy, FastAPI With MongoDB, Fastapi Postgresql Docker
- **Performance & Caching**: Caching in FastAPI Applications, Redis in FastAPI, Pagination with FastAPI
- **Background Processing**: Celery in FastAPI, Fastapi Background Tasks, Schedule Your Job with Apscheduler
- **API Enhancement**: Fastapi Documentation, Fastapi Metadata Configuration, SSE in FastAPI Application
- **Infrastructure**: Fastapi with Middleware, Exceptions In FastAPI, FastAPI with Python Logging
- **Real-time Features**: Websocket in Fastapi, Slow-Polling FastAPI
- **Testing & Quality**: Pytest Testing With FastAPI, Profiling In FastAPI

### Root Level Files
- `pyproject.toml` - Main dependency management using modern Python packaging
- `uv.lock` - Lock file for reproducible dependencies  
- `.venv/` - Virtual environment (use this for all Python commands)
- `requirements.txt` - Legacy requirements file (mostly empty, use pyproject.toml)

## Canonical Project Layout

Most projects follow this pattern (using "CRUD Operation With SQLAlchemy" as reference):

```
Project Name/
├── main.py          # FastAPI app instance and endpoint definitions
├── models.py        # SQLAlchemy database models (if using SQLAlchemy)
├── schemas.py       # Pydantic models for request/response validation
├── databases.py     # Database connection and session management
├── __init__.py      # Makes directory a Python package
├── README.md        # Project-specific documentation
└── test_*.py        # Test files (if present)
```

### Architectural Patterns

**1. Simple Single-File Apps**
```python
# Direct approach - everything in main.py
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}
```

**2. Layered Architecture (Recommended)**
```python
# main.py - FastAPI app and routes only
from fastapi import FastAPI, Depends
from .schemas import ItemCreate, Item
from .models import get_db

app = FastAPI()

@app.post("/items")
def create_item(item: ItemCreate, db: Session = Depends(get_db)) -> Item:
    # Business logic here
```

**3. Class-Based Handlers** (JWT Authentication pattern)
```python
# Separation of concerns with handler classes
class AuthHandler:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"])
    
    async def authenticate_user(self, username: str, password: str):
        # Authentication logic
```

**4. Middleware Integration**
```python
# Custom middleware for cross-cutting concerns
app.add_middleware(ResourceBaseMiddleware)
```

## Development & Debugging Tips

### Database Projects
- Most SQLAlchemy projects use in-memory SQLite for demos
- Database tables auto-create on startup via `@app.on_event("startup")`  
- Check `databases.py` for connection strings and session management

### Docker Projects
```powershell
# For Docker-enabled projects (e.g., "Fastapi Postgresql Docker")
docker-compose up --build

# Access at http://localhost:8000
# PostgreSQL at localhost:5432
```

### Common Issues & Solutions
- **Import Errors**: Ensure you're in `.venv` and project root directory
- **Database Errors**: Check if database containers are running (for Docker projects)
- **Port Conflicts**: Default port 8000, change with `--port 8001`
- **Cookie Expiry**: JWT projects handle token expiration - check auth handlers for refresh logic

### Debugging FastAPI Apps
```powershell
# Run with debug logging
.\.venv\Scripts\uvicorn.exe "main:app" --reload --log-level debug

# Interactive API docs always at /docs
# Alternative docs at /redoc
```

## Testing Guide

### Projects with Tests
- **Pytest Testing With FastAPI** - Complete testing example
- **Exceptions In FastAPI** - Error handling tests

### Test Patterns
```python
# Standard test setup pattern
from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == "server is running"
```

### Database Testing Pattern
```python
# Override database dependency for testing
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, poolclass=StaticPool)

def override_get_db():
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()

app.dependency_overrides[get_db] = override_get_db
```

### Running Tests by Category
```powershell
# Test all database-related projects
.\.venv\Scripts\pytest.exe -k "CRUD|MongoDB|Postgresql" -v

# Test authentication projects  
.\.venv\Scripts\pytest.exe -k "JWT|Auth" -v

# Test with specific markers (if defined)
.\.venv\Scripts\pytest.exe -m "integration" -v
```

## Reusable Patterns & Code Snippets

### 1. Database Session Management
```python
# Standard SQLAlchemy setup (from CRUD example)
from sqlalchemy.orm import Session

def get_db():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
```

### 2. JWT Authentication Wrapper
```python
# From JWT Authentication project
async def auth_wrapper(self, auth: HTTPAuthorizationCredentials = Security(security)):
    token = auth.credentials
    if not token or await self.istokenblock(token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Decode and validate token...
```

### 3. Error Handling Pattern
```python
# From Exceptions project
from fastapi import HTTPException

@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message}
    )
```

### 4. Background Task Pattern  
```python
# From Background Tasks project
from fastapi import BackgroundTasks

@app.post("/send-email/")
async def send_email(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email_task, email_data)
    return {"message": "Email will be sent"}
```

### 5. Dependency Injection Pattern
```python
# Common pattern across projects
from fastapi import Depends

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # User validation logic
    return user

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"user": current_user}
```

## Project-Specific Notes

### High-Value Reference Projects
- **"CRUD Operation With SQLAlchemy"** - Best example of clean layered architecture
- **"Pytest Testing With FastAPI"** - Complete testing patterns and setup
- **"JWT Authentication In FastAPI"** - Production-ready auth implementation  
- **"Fastapi Postgresql Docker"** - Docker containerization best practices
- **"Fastapi with Middleware"** - Custom middleware implementation

### External Dependencies
Many projects require additional services:
- **Redis projects**: Need Redis server running
- **Celery projects**: Require message broker (RabbitMQ/Redis)
- **MongoDB projects**: Need MongoDB instance
- **PostgreSQL projects**: Database server required

### Output & Window Preferences
- Use `--reload` for development to see changes immediately
- FastAPI automatically opens to windowed output showing request logs
- Interactive documentation always available at `/docs` endpoint for testing API calls
- Use `pytest -v` for verbose test output in window mode

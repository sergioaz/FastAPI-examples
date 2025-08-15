## FastAPI with Middleware

### Description:
This repository contains a FastAPI project template integrated with middleware, showcasing how to incorporate middleware into your FastAPI application. Middleware in FastAPI allows you to intercept requests and responses, enabling various functionalities such as authentication, logging, error handling, etc., in a centralized manner.

### Middleware Logging Features:

This project demonstrates two types of middleware logging implementations:

#### 1. Custom Middleware Logging (`middleware.py`)
The `MyMiddleware` class provides:
- **Request Interception**: Logs "I'm a middleware!" message for each incoming request
- **Performance Monitoring**: Measures and logs execution time for each request
- **Response Time Tracking**: Calculates the time difference between request start and response completion

```python
class MyMiddleware:
    async def __call__(self, request: Request, call_next):
        print("I'm a middleware!")
        start_time = time.time()            
        response = await call_next(request)
        end_time = time.time()
        print("execution time: {} seconds".format(end_time - start_time))
        return response
```

#### 2. HTTP Request Logging Middleware (`main.py`)
The built-in HTTP middleware provides:
- **Request Method Logging**: Captures HTTP method (GET, POST, PUT, etc.)
- **URL Path Logging**: Records the requested endpoint path
- **Structured Logging**: Uses Python's logging module with INFO level

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming {request.method} {request.url.path}")
    response = await call_next(request)
    return response
```

#### Logging Configuration:
- **Log Level**: Set to INFO level for detailed request tracking
- **Logger Instance**: Uses module-specific logger (`__name__`)
- **Console Output**: All middleware logs are displayed in the console during development

#### Use Cases:
- **Debugging**: Track incoming requests and identify slow endpoints
- **Performance Monitoring**: Measure response times for optimization
- **Audit Trail**: Maintain logs of all API interactions
- **Error Tracing**: Correlate requests with potential issues

### Installation:
Clone the repository:

```bash
git clone https://github.com/rajansahu713/FastAPI-Projects.git
```

Navigate to the Fastapi with Middleware directory:

```bash
cd FastAPI-Projects/Fastapi\ with\ Middleware
```

Install dependencies using pip:

```bash
pip install fastapi
```

Run the FastAPI application:

```bash
uvicorn main:app --reload

Once the server is running, you can access the API documentation at http://localhost:8000/docs.
```

### Contact:
For any inquiries or suggestions regarding this project, you can reach out to the project owner here.
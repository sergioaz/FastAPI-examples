# Fastapi Metadata Configuration

This project demonstrates how to configure metadata for a FastAPI application, including custom title, description, version, documentation URLs, and global dependencies. It also shows how to handle maintenance mode and configure CORS middleware.

## Features
- Custom FastAPI metadata (title, description, version, docs URL)
- Global dependency for maintenance mode
- Custom exception handling for maintenance
- CORS middleware configuration

## Example Usage

1. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn
   ```
2. **Run the application:**
   ```bash
   uvicorn main:app --reload
   ```
3. **Access the docs:**
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

## main.py Overview
- Sets FastAPI metadata (title, description, version, docs URL)
- Adds a global dependency to check for maintenance mode
- Handles `UnderMaintenanceException` with a custom response
- Configures CORS to allow specific methods

## Example Endpoint
```python
@app.get("/r")
def read_root():
    return {"Hello": "World"}
```

## License
MIT


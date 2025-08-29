from fastapi import APIRouter, Depends, FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from user_exceptions import UserNotFoundException
from exception_handlers import user_not_found_handler

"""
example of creating and handling custom exceptions in FastAPI.
"""
def get_user_from_db(user_id: int):
    return None  # Simulate user not found

app = FastAPI()

# Step 3: Register It in Your App
app.add_exception_handler(UserNotFoundException, user_not_found_handler)

# Handle Common Errors Globally
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request", "errors": exc.errors()},
    )

@app.get("/user/{user_id}")
def get_user(user_id: int):
    user = get_user_from_db(user_id)
    if not user:
        raise UserNotFoundException(user_id)
    return user

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

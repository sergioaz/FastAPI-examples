from fastapi import Request
from fastapi.responses import JSONResponse
from user_exceptions import UserNotFoundException

async def user_not_found_handler(request: Request, exc: UserNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": f"User with ID {exc.user_id} not found"},
    )
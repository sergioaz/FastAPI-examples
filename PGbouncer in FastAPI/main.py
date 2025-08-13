import asyncpg
from fastapi import Depends, FastAPI, Path, HTTPException
from database import DataBasePool, DatabaseConnection, execute_query_with_pool, execute_query
from contextlib import asynccontextmanager
from models import UserIdResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle the lifespan of the FastAPI application for resource setup and teardown.
    Parameters:
        - app (FastAPI): The FastAPI application instance.
    Returns:
        - None: This function does not return anything.
    Example:
        - No direct usage example as this function is used internally by FastAPI.
    """
    await DataBasePool.setup()  # Initialize pool
    await DatabaseConnection.setup()  # Initialize connection

    try:
        yield
    finally:
        await DataBasePool.teardown()
        await DatabaseConnection.teardown()


app = FastAPI(lifespan=lifespan)

@app.get("/with_pool/{user_id}", response_model=UserIdResponse)
async def handle(db_pool:asyncpg.Pool = Depends(DataBasePool.get_pool), user_id: int = Path(..., description="User ID")):
    """
    Asynchronously handles a database transaction to fetch the user using connection pool
    Parameters:
        - db_pool (asyncpg.Pool): Database connection pool, provided by dependency injection with a default of DataBasePool.get_pool.
        - user_id: The ID of the user to fetch
    Returns:
        - UserIdResponse: A user record with all required fields
    Example:
        - handle(db_pool, 1) -> {"id": 1, "username": "john", ...}
    """

    async with db_pool.acquire() as connection:
        async with connection.transaction():
            query = f"SELECT * FROM users where id = {user_id}"
            result = await execute_query_with_pool(query, fetch_one=True)
            
            # Convert asyncpg.Record to dictionary
            if result:
                return dict(result)
            else:
                # Handle case where user is not found
                raise HTTPException(status_code=404, detail="User not found")

@app.get("/without_pool/{user_id}", response_model=UserIdResponse)
async def without_pool(user_id: int = Path(..., description="User ID")):
    """
    Execute a SQL query to fetch a user record without using a connection pool.
    Parameters:
        user_id: The ID of the user to fetch
    Returns:
        - UserIdResponse: A user record with all required fields
    Example:
        - without_pool(1) -> {"id": 1, "username": "john", ...}
    """
    query = f"SELECT * FROM users where id = {user_id}"
    data = await execute_query(query, fetch_one=True)
    
    # Convert asyncpg.Record to dictionary
    if data:
        return dict(data)
    else:
        # Handle case where user is not found
        raise HTTPException(status_code=404, detail="User not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import FastAPI
from fastapi import Request

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.exc import SQLAlchemyError

class SQLAlchemySessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, db_session_factory):
        super().__init__(app)
        self.db_session_factory = db_session_factory

    async def dispatch(self, request: Request, call_next):
        request.state.db = self.db_session_factory()
        try:
            response = await call_next(request)
            request.state.db.commit()
        except SQLAlchemyError:
            request.state.db.rollback()
            raise
        finally:
            request.state.db.close()
        return response



app = FastAPI()
app.add_middleware(SQLAlchemySessionMiddleware, db_session_factory=SessionLocal)



@app.get("/users")
def read_users(request: Request):
    db = request.state.db
    users = db.query(User).all()
    return users
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import redis.asyncio as redis
from contextlib import asynccontextmanager
import asyncio

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    FastAPICache.init(RedisBackend(r), prefix="fastapi-cache")
    yield

app.router.lifespan_context = lifespan

from fastapi_cache.decorator import cache

@app.get("/products")
@cache(expire=60)  # cache for 60 seconds
async def get_products():
    # Simulate DB or computation
    await asyncio.sleep(1)
    return {"products": ["Laptop", "Phone", "Tablet"]}
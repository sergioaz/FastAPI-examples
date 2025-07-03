[Link text](https://medium.com/the-pythonworld/15-useful-middlewares-for-fastapi-that-you-should-know-about-8c2d67ea0d86)

# Cache Middleware 
Use caching to reduce redundant processing and database queries — speeding up your FastAPI endpoints dramatically.

> uv pip install fastapi-cache2[redis]

```language

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import redis.asyncio as redis

app = FastAPI()

@app.on_event("startup")
async def startup():
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    FastAPICache.init(RedisBackend(r), prefix="fastapi-cache")
```

### Inline Code
`inline code`

### Code Block
```python

def hello_world():
    return "Hello, World!"
```

---
> This is a blockquote.
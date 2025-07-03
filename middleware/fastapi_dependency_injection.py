from typing import Protocol
from fastapi import FastAPI, Depends

class TokenStore(Protocol):
    async def lookup(self, token: str) -> str | None: ...


from typing import Annotated

app = FastAPI()

@app.get("/profile")
async def read_profile(
    token: str,
    store: Annotated[TokenStore, Depends()],
):
    return await store.lookup(token)

class MemoryStore:
    def __init__(self) -> None:
        self._tokens = {"demo": "alice"}

    async def lookup(self, token: str) -> str | None:
        return self._tokens.get(token)



single_store = MemoryStore()
app.dependency_overrides[TokenStore] = lambda: single_store
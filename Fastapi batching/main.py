from pydantic import BaseModel
from typing import List, Literal, Optional
import asyncio
from fastapi import APIRouter, Depends, FastAPI
# from .services import fetch_profile, fetch_settings, fetch_notifications, fetch_suggestions

app = FastAPI(
    title="Address Search API",
    description="API for searching addresses using Elasticsearch with comparison capabilities",
    version="1.0.0",
    #lifespan=lifespan
)

router = APIRouter()


class BatchRequest(BaseModel):
    operations: List[Literal["profile", "settings", "notifications", "suggestions"]]

class  ProfileOut(BaseModel):
    profile: str = "Default profile"

class SettingsOut(BaseModel):
    settings: str = "Default settings"

class Notification(BaseModel):
    notification: str = "Default notification"

class Suggestion(BaseModel):
    suggestion: str = "Default suggestion"

class BatchResponse(BaseModel):
    profile: Optional[ProfileOut]
    settings: Optional[SettingsOut]
    notifications: Optional[List[Notification]]
    suggestions: Optional[List[Suggestion]]

async def fetch_profile():
    return {"profile":"Profile 1"}

async def fetch_settings():
    return {"settings":"Setting 1"}

async def fetch_notifications():
    return {"notifications": "fetch_notifications 1"}

async def fetch_suggestions():
    return {"suggestions": ["fetch_suggestions 1", "fetch_suggestions 2"]}



@router.post("/batch")
async def batch_response(req: BatchRequest):
    tasks = []
    if "profile" in req.operations:
        tasks.append(fetch_profile())
    else:
        tasks.append(None)
    if "settings" in req.operations:
        tasks.append(fetch_settings())
    else:
        tasks.append(None)
    if "notifications" in req.operations:
        tasks.append(fetch_notifications())
    else:
        tasks.append(None)
    if "suggestions" in req.operations:
        tasks.append(fetch_suggestions())
    else:
        tasks.append(None)
    res = {}
    responses = await asyncio.gather(*[task for task in tasks if task])

    # add responses into res
    for d in responses:
        res.update(d)

    return res

app.include_router(router)

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
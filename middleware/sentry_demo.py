from fastapi import FastAPI
import sentry_sdk

def risky_operation():
    # Simulate a risky operation that might fail
    raise ValueError("This is a simulated error for Sentry tracking.")

sentry_sdk.init(
    dsn="https://4e1dcbf812bb2156351a04054f3bb0bb@o4509600462667776.ingest.us.sentry.io/4509600464961536",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    # environment="staging",
    # traces_sample_rate=0.2,  # sample 20% of requests
)

app = FastAPI()

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0


# Monitor Background Tasks Too
# track exceptions from Celery, RQ, or asyncio background jobs
from sentry_sdk import capture_exception

try:
    risky_operation()
except Exception as e:
    capture_exception(e)

# add some data
from sentry_sdk import set_user, set_tag

@app.middleware("http")
async def enrich_sentry(request, call_next):
    set_user({"id": "user_123", "email": "aashish@example.com"})
    set_tag("env", "production")
    response = await call_next(request)
    return response


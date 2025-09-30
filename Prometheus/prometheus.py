from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter
import prometheus_client


instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    env_var_name="ENABLE_METRICS",
)



app = FastAPI()

# Create instrumentator instance
instrumentator = Instrumentator().instrument(app).expose(app)
instrumentator.instrument(app).expose(app, include_in_schema=False)

# Define a custom counter metric
try:
    my_counter = prometheus_client.REGISTRY._names_to_collectors['my_custom_counter']
except KeyError:
    my_counter = Counter("my_custom_counter", "Description of my custom counter")

@app.get("/ping")
async def ping():
    my_counter.inc()
    return {"message": "pong"}

def main():
    import uvicorn
    print (f"{__file__=}")
    uvicorn.run(
        "prometheus:app",
        host="localhost",
        port=8000,
        # reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()


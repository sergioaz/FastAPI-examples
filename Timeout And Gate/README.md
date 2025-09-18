# How to run FastAPI in production:

## Run uvicorn with uvloop, keep the worker model boring

Why it helps: 
- uvloop shrinks scheduling overhead; 
- httptools keeps HTTP/1.1 parsing lean; 
- finite --limit-concurrency prevents meltdown when bursts arrive.

`bash`
uvicorn app:app \
  --loop uvloop \
  --http httptools \
  --workers $((2 * $(nproc))) \
  --backlog 2048 \
  --timeout-keep-alive 5 \
  --limit-concurrency 1500
``

## For multi-process orchestration and clean restarts, many teams prefer Gunicorn with uvicorn workers:
`bash`
gunicorn app:app \
  -k uvicorn.workers.UvicornWorker \
  -w $((2 * $(nproc))) \
  --reuse-port --backlog 2048 --timeout 0

## Fast serialization, zero wasted bytes
- Goal: small, easy-to-parse payloads that the CPU can sprint through.

### Make ORJSON your default serializer:
`python`
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)
``

- Prefer flat objects over Russian-doll nesting. Clients read them faster too.
- Stream when payloads are large; compress only when it pays off (Brotli q=3–4 for >1 KB, otherwise skip).
- With Pydantic v2 models, pre-compile and reuse schema; avoid per-request json.dumps with custom hooks.

## Why it helps: most APIs spend more time in (de)serialization than you think. Cutting 5–10 ms here is common.
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
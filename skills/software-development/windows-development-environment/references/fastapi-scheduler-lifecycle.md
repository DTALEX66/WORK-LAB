# FastAPI + APScheduler Lifecycle on Windows

## The lifespan pattern

Use FastAPI's `lifespan` context manager (not `on_event` decorator, which is deprecated) to start/stop background schedulers:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await start_scheduler()
    yield
    # Shutdown
    await stop_scheduler()

app = FastAPI(lifespan=lifespan)
```

## APScheduler with async

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def start_scheduler():
    scheduler.add_job(
        my_async_func,
        "interval",
        minutes=60,
        id="my_job",
        replace_existing=True,
    )
    scheduler.start()

async def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
```

## Manual trigger pattern

Provide an API endpoint for manual execution:

```python
@router.post("/trigger")
async def trigger():
    await my_async_func()
    return {"status": "ok"}
```

## Testing strategy

Write a `tests/test_api.py` that starts the server (via background terminal), then runs assertions:

```python
import httpx, asyncio

async def test():
    async with httpx.AsyncClient() as c:
        r = await c.get("http://localhost:8766/api/health")
        assert r.status_code == 200

        r = await c.post("http://localhost:8766/api/people/", json={
            "uid": "p1", "name": "test", "person_type": "star"
        })
        assert r.status_code == 201

        r = await c.get("http://localhost:8766/api/discovery/trigger")
        assert r.status_code == 200

if __name__ == "__main__":
    success = asyncio.run(test())
```

## Port conflict resolution

Before restarting the dev server, explicitly kill the old process:

```bash
# Node.js helper to find and kill
node -e "
const { execSync } = require('child_process');
const result = execSync('netstat -ano | findstr :8766', {encoding:'utf8'});
const pids = [...new Set(result.split('\\n')
  .filter(l => l.includes('LISTEN'))
  .map(l => l.trim().split(/\\s+/).pop())
  .filter(Boolean))];
pids.forEach(pid => { execSync('taskkill /F /PID ' + pid, {stdio:'ignore'}); });
"
```

## Directory structure pattern

```
packages/my-service/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app + lifespan
│   ├── config.py          # pydantic-settings
│   ├── database.py        # SQLAlchemy async engine + session
│   ├── models.py          # ORM models
│   ├── schemas.py         # Pydantic schemas
│   ├── routers/           # Route modules
│   │   ├── health.py
│   │   └── my_resource.py
│   ├── services/          # Business logic
│   │   └── rsshub.py
│   └── tasks/             # Scheduler tasks
│       └── scheduler.py
├── tests/
│   └── test_api.py
├── requirements.txt
├── .env.example
└── .gitignore             # <-- include .venv/ here!
```

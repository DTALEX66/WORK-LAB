# Python FastAPI + SQLAlchemy Async on Windows

Common pitfalls and fixes when setting up async Python backends (FastAPI + SQLAlchemy async + SQLite) on Windows.

## Async SQLAlchemy greenlet error

```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called;
can't call await_only() here. Was IO attempted in an unexpected place?
```

### Cause

Accessing SQLAlchemy ORM relationships (`.sources`, `.discoveries`) outside an async context triggers lazy loading, which requires a greenlet. This happens when constructing response objects that iterate over relationships.

### Fix — eager-load with `selectinload`

```python
from sqlalchemy.orm import selectinload

# WRONG — lazy loading will fail
result = await db.execute(select(Person))

# RIGHT — eager load relationships
result = await db.execute(
    select(Person)
    .options(selectinload(Person.sources), selectinload(Person.discoveries))
)
```

### Fix — avoid `__dict__` serialization for Pydantic

```python
# WRONG — triggers lazy loading + dict key issues
return PersonResponse(
    **{k: v for k, v in person.__dict__.items() if k != '_sa_instance_state'},
    source_count=len(person.sources),  # 💥 greenlet error
)

# RIGHT — use explicit fields
def _person_to_response(p: Person) -> PersonResponse:
    return PersonResponse(
        id=p.id, uid=p.uid, name=p.name,
        source_count=len(p.sources),  # safe with selectinload loaded
        discovery_count=len(p.discoveries),
    )
```

## Windows-specific curl issues for API testing

When testing a FastAPI backend running on `localhost` from Git Bash (MSYS2):

### JSON body with double quotes gets mangled

```bash
# WRONG — MSYS2 treats single quotes differently and JSON parsing fails
curl -X POST http://localhost:8000/api/people/ \
  -H "Content-Type: application/json" \
  -d '{"uid":"p1","name":"test"}'
# → {"detail":"There was an error parsing the body"}

# FIX — Use a Python test script instead:
python -c "
import httpx, asyncio
async def test():
    async with httpx.AsyncClient() as c:
        r = await c.post('http://localhost:8000/api/people/', json={
            'uid': 'p1', 'name': 'test'
        })
        print(r.status_code, r.json())
asyncio.run(test())
"
```

Or use a dedicated `tests/test_api.py` file.

## Python venv path

On Windows, always create the venv inside the project:

```bash
cd project/packages/my-service
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --port 8766
```

**Key difference from macOS/Linux:**
- Activate: `.venv/Scripts/activate` (not `bin/activate`)
- Python: `.venv/Scripts/python.exe` (not `bin/python`)
- Pip: `.venv/Scripts/pip.exe`
- Use `.venv/Scripts/pip install` or `.venv/Scripts/python -m pip install`

## Port conflicts when restarting

On Windows, killed server processes may hold the port for several seconds:

```bash
# Find and kill process holding port 8766
netstat -ano | findstr :8766
# → TCP 0.0.0.0:8766 0.0.0.0:0 LISTENING 12345
taskkill /F /PID 12345
```

Use a Node.js helper to automate this:
```javascript
const { execSync } = require('child_process');
const result = execSync('netstat -ano | findstr :8766', {encoding:'utf8'});
const pids = [...new Set(result.split('\n')
  .filter(l => l.includes('LISTEN'))
  .map(l => l.trim().split(/\s+/).pop()))];
pids.forEach(pid => { if (pid && pid !== '0') execSync('taskkill /F /PID ' + pid); });
```

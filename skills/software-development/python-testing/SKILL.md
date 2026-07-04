---
name: python-testing
description: "Python testing patterns, gotchas, and conventions for unittest/pytest."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [testing, python, unittest, pytest, gotchas]
    related_skills: [test-driven-development]
---

# Python Testing Patterns & Gotchas

## When to Use

When writing Python tests with `unittest` or `pytest`.

## `assertIn` on Lists is Element Membership, Not Substring

```python
# WRONG — this FAILS:
self.assertIn('missing reasoning', result.gaps)
# Checks exact element match, not substring!

# RIGHT — check for substring across elements:
self.assertTrue(any('missing reasoning' in g for g in result.gaps))
```

## `assertEqual` with Floats

```python
# Use assertAlmostEqual for floats:
self.assertAlmostEqual(0.1 + 0.2, 0.3, places=6)
```

## `assertRaises` Requires Context Manager

```python
# RIGHT:
with self.assertRaises(ValueError):
    int('abc')
```

## Fixture Scoping

| Scope | Method | When |
|-------|--------|------|
| Per-test | `setUp()` / `tearDown()` | Every test needs isolation |
| Per-class | `setUpClass()` / `tearDownClass()` | Once per test class |
| Per-module | `setUpModule()` / `tearDownModule()` | Once per test file |

## Python `re` — Variable-Width Lookbehind Error

Python's `re` module does NOT support variable-width lookbehinds.

```python
# WRONG — Python 3.11+ raises:
re.findall(r'(?<!\w)(?<!\n\s*)(?<!#)#([\w\-/]+)', text)

# RIGHT — merge into fixed-width:
re.findall(r'(?<![#\w])#([\w\-/]+)', text)
```

## `\s` in Character Classes Matches Newlines

```python
# WRONG — \s inside [...] matches \n too
re.compile(r'^([\w\s]+)::\s*(.+)$', re.MULTILINE)

# RIGHT — use only space:
re.compile(r'^([\w ]+)::\s*(.+)$', re.MULTILINE)
```

## WindowsPath Missing `is_relative()`

Python 3.11+ Windows: `WindowsPath` has NO `is_relative()`.

```python
# RIGHT — use try/except:
try:
    rel_path = resolved_path.relative_to(PROJECT_ROOT)
except ValueError:
    rel_path = str(resolved_path)
```

## Reporting Task

```bash
python -m unittest discover -s tests
```

## SQLite Testing: Persistent State Across Tests

When testing SQLite-backed code, the database file persists across test runs.
Searches may return stale data from previous test executions, causing
`results[0]["id"] == expected_id` to fail even when your test correctly
inserted the record.

**Fix**: use `any()` for existence checks instead of positional assertions:

```python
# WRONG — fails when previous runs left data in the DB:
results = search_core_objects("MVP development", top_k=5)
assert results[0]["id"] == "test_obj_001"

# RIGHT — checks that your record exists somewhere in results:
results = search_core_objects("MVP development", top_k=5)
assert any(r["id"] == "test_obj_001" for r in results)
```

**Alternative**: clean the database in `setUp()` or use an in-memory SQLite
(`:memory:`) for isolated test runs:

```python
class TestSQLite:
    def setup_method(self):
        # Use in-memory DB or delete the file before each test
        import app.memory.database as db
        db.DB_PATH = Path(":memory:")  # or temp file
        db.init_db()
```

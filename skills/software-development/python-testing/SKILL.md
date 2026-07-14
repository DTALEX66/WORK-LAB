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

## Monorepo Testing & Dedup Patterns

Key patterns:
- Subdirectory test imports with `sys.path` for hyphen-named directories
- SQL-free service module testing (pass `list[dict]` instead of querying DB)
- OS-specific `pytest.raises` match patterns
- Dataclass with defaults — no TypeError on empty init

## Similarity / Vector Search Tests Need Strong Anchors

Embedding and vector-search tests can be flaky when the “relevant” sample does not actually share query terms or strong semantic anchors. Hash/ngram embedders especially may rank an unrelated short text above a vaguely related text.

```python
# WEAK — query terms are absent from the expected top document; ranking may drift:
index_card("c1", "backpropagation algorithm explained")
index_card("c2", "how to make pizza dough")
results = search_cards("neural network training", top_k=2)
assert results[0][0] == "c1"

# STRONG — expected document contains the query anchors being asserted:
index_card("c1", "neural network training backpropagation algorithm explained")
index_card("c2", "how to make pizza dough")
results = search_cards("neural network training", top_k=2)
assert results[0][0] == "c1"
```

If a test is meant to verify no-error behavior rather than exact ranking, assert shape/count or membership instead of first-place ordering.

## SQLite Testing: Persistent State Across Tests

When testing SQLite-backed code, the database file persists across test runs.
Searches may return stale data from previous test executions, causing
`results[0]["id"] == expected_id` to fail even when your test correctly
inserted the record.

**Fix**: use `any()` for existence checks instead of positional assertions, and make the query window large enough for persistent DB tables:

```python
# WRONG — fails when previous runs left data in the DB or limit is too small:
results = search_core_objects("MVP development", top_k=5)
assert results[0]["id"] == "test_obj_001"

traces = list_traces_db(limit=10)
assert any(t["id"] == "trace_test_001" for t in traces)  # may be crowded out

# RIGHT — checks that your record exists somewhere in a wide enough result set:
results = search_core_objects("MVP development", top_k=50)
assert any(r["id"] == "test_obj_001" for r in results)

traces = list_traces_db(limit=500)
assert any(t["id"] == "trace_test_001" for t in traces)
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

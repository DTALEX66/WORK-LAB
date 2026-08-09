---
name: workflow-assistance-python-testing
description: "Use when writing, changing, debugging, or running Python tests with unittest, pytest, virtual environments, or Windows path constraints."
---

# Python testing

- Inspect `pyproject.toml`, lock files, test configuration, neighboring tests, and the actual interpreter before choosing commands.
- On Windows, distinguish `python`, `python3`, `pip`, and project virtual environments; do not assume they point to the same interpreter.
- For new behavior or a bug fix, write a focused failing test, observe the expected failure, implement the minimum fix, and rerun it.
- Use real filesystem and process behavior when practical; avoid tests that only prove mock configuration.
- Put temporary environments and caches inside the project runtime boundary.
- Run the smallest targeted test first, then the owning module's broader suite and canonical gate.
- Report skipped tests and warnings separately; do not hide them inside a pass count.

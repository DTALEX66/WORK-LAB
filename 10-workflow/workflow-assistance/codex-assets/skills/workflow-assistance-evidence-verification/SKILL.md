---
name: workflow-assistance-evidence-verification
description: "Use when verifying implementation, builds, tests, desktop/runtime behavior, CI, publication, releases, or completion claims."
---

# Evidence verification

Classify evidence before claiming completion:

1. Structural: files, schemas, static checks, and source inspection.
2. Local execution: tests, builds, and runtime checks on the current checkout.
3. Exact-SHA CI: required remote jobs for the precise commit.
4. Publication: remote branch, package, release, installer, or URL readback.
5. Live behavior: the actual target runtime restarted and behaviorally verified.

Run required checks from the owning module. A failed, cancelled, missing, or required-but-skipped check is not a pass. Fixtures, screenshots of source, documentation, version strings, and local tests cannot substitute for higher evidence levels.

Finish with explicit `PASS`, `PARTIAL`, `NOT EXECUTED`, and `BLOCKED` states plus the command, path, SHA, URL, or runtime handle that grounds each claim.

For Git identity evidence, use explicit refs (`git rev-parse HEAD`, `git rev-parse origin/<branch>`) instead of upstream shorthand; if a command dies with a shell parse error (e.g. PowerShell "hashtable not terminated"), re-issue with explicit refs and record the quoting failure separately from repository state.

When a Windows command fails, classify the failure class before retrying: quoting/parsing (hashtable or subexpression mangling), MSYS path conversion (a `/...` argument became `C:/Program Files/Git/...`), encoding (UTF-16 artifacts, mojibake), line endings ("bad interpreter" on a CRLF script), or file lock ("file in use"). Re-issue the dialect-correct form (single quotes, `MSYS_NO_PATHCONV=1`, UTF-8, LF + `.gitattributes`, wait for the lock) and record the class — never retry the identical string.

External scanner or agent reports (e.g. OpenHuman junction/duplicate/path findings) are candidate claims, not facts. Verify with native tools on the exact path (`fsutil reparsepoint query` returns a tag for junctions and error 4390 for real directories; `Get-Item` LinkType/Target shows the reparse bit), compare content when a "duplicate" is claimed, and use git HEAD/cloud readback for deletion claims. Classify each finding `CONFIRMED` / `REFUTED` / `NEEDS_PATH` and record it; never act on an unverified scanner label.

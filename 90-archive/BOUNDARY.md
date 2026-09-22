# BOUNDARY marker — 90-archive/ (WORK-LAB V2, three-project split)

Classification: HISTORY_ONLY_CONVERGE
Authority: .project/governance/three-project-boundary.json (boundary_splits[ARCHIVE_90])

## Problem
Root-level `90-archive/` is a SECOND history retrieval system alongside
`docs/history/`. Two anchors for one retrieval surface is exactly the
drift the V2 convergence forbids.

## Converge
- 90-archive/ holds frozen historical reports (e.g. reports-history). It is
  evidence, not an active module. No production code imports it (0 refs).
- Single history retrieval anchor = docs/history/. 90-archive/ is recorded
  as a history-only directory that must not grow as an active owner.
- No file moves this round; the boundary verifier forbids a new root-level
  second history system and keeps 90-archive/ as history-only.

## Status: marked + gated. No file moves this round.

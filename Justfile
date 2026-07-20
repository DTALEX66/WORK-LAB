# Optional convenience wrapper. The canonical entry point is the Python runner:
#   python scripts/workflow/run_quality_gate.py verify
# just is not a required dependency for this portable pack.

set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

_default:
    @python scripts/workflow/run_quality_gate.py list

verify:
    python scripts/workflow/run_quality_gate.py verify

governance:
    python scripts/workflow/run_quality_gate.py governance

compile:
    python scripts/workflow/run_quality_gate.py compile

security:
    python scripts/workflow/run_quality_gate.py security

context-pack:
    python scripts/workflow/run_quality_gate.py context-pack

shell:
    python scripts/workflow/run_quality_gate.py shell

powershell:
    python scripts/workflow/run_quality_gate.py powershell

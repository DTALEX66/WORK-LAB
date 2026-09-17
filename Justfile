# Optional convenience wrapper. The canonical entry point is the Python runner:
#   python services/orchestration/run_quality_gate.py verify
# just is not a required dependency for this portable pack.

set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

_default:
    @python services/orchestration/run_quality_gate.py list

verify:
    python services/orchestration/run_quality_gate.py verify

governance:
    python services/orchestration/run_quality_gate.py governance

compile:
    python services/orchestration/run_quality_gate.py compile

skill-provenance:
    python services/orchestration/run_quality_gate.py skill-provenance

security:
    python services/orchestration/run_quality_gate.py security

context-pack:
    python services/orchestration/run_quality_gate.py context-pack

portable-install:
    python services/orchestration/run_quality_gate.py portable-install

portable-install-runtime:
    python services/orchestration/run_quality_gate.py portable-install-runtime

provider-inventory:
    python services/orchestration/run_quality_gate.py provider-inventory

mcp-audit:
    python services/orchestration/run_quality_gate.py mcp-audit

shell:
    python services/orchestration/run_quality_gate.py shell

powershell:
    python services/orchestration/run_quality_gate.py powershell

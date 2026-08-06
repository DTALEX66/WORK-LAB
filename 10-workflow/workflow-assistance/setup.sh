#!/bin/bash
# Plan-first Workflow-assistance installer. Hermes Agent itself must already exist for apply.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
if [ -z "${HERMES_HOME:-}" ]; then
    case "$(uname -s 2>/dev/null || echo unknown)" in
        MINGW*|MSYS*|CYGWIN*) HERMES_HOME="${LOCALAPPDATA:-$HOME/AppData/Local}/hermes" ;;
        *) HERMES_HOME="$HOME/.hermes" ;;
    esac
fi
export HERMES_HOME

APPLY=0
PLAN_FILE="$REPO_ROOT/.hermes/task-artifacts/setup-plan.json"
while [ "$#" -gt 0 ]; do
    case "$1" in
        --apply) APPLY=1 ;;
        --plan-json)
            [ "$#" -ge 2 ] || { echo "--plan-json requires a path" >&2; exit 2; }
            PLAN_FILE="$2"
            shift
            ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
done

PY_REPO_ROOT="$REPO_ROOT"
PY_HERMES_HOME="$HERMES_HOME"
PY_PLAN_FILE="$PLAN_FILE"
SHELL_HERMES_HOME="$HERMES_HOME"
case "$(uname -s 2>/dev/null || echo unknown)" in
    MINGW*|MSYS*|CYGWIN*)
        if command -v cygpath >/dev/null 2>&1; then
            PY_REPO_ROOT="$(cygpath -w "$REPO_ROOT")"
            PY_HERMES_HOME="$(cygpath -w "$HERMES_HOME")"
            PY_PLAN_FILE="$(cygpath -w "$PLAN_FILE")"
            SHELL_HERMES_HOME="$(cygpath -u "$HERMES_HOME")"
        fi
        ;;
esac

if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN=python
elif command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
    PYTHON_BIN=python3
else
    echo "a working python or python3 is required" >&2
    exit 1
fi
[ -d "$HERMES_HOME" ] || { echo "Hermes home must already exist; refusing to create a live target: $HERMES_HOME" >&2; exit 1; }

SYNC_ARGS=(
    "$PY_REPO_ROOT/scripts/workflow/sync_hermes_workflow_assets.py"
    --repo "$PY_REPO_ROOT"
    --home "$PY_HERMES_HOME"
    --plan-json "$PY_PLAN_FILE"
)
if [ "$APPLY" -eq 1 ]; then
    command -v hermes >/dev/null || { echo "Hermes Agent is required for --apply plugin readback" >&2; exit 1; }
    SYNC_ARGS+=(--apply --approved)
fi

"$PYTHON_BIN" "${SYNC_ARGS[@]}"

if [ "$APPLY" -eq 0 ]; then
    echo "ACTION_PLAN_ONLY path=$PLAN_FILE"
    echo "No live files or plugins were changed. Review the plan, then rerun with --apply."
    exit 0
fi

# Git checkouts created on Windows can lose POSIX executable bits. Restore only
# the known installer-owned executable after the atomic sync succeeds.
chmod +x "$SHELL_HERMES_HOME/bin/hermes-npx"

# Required plugins are fail-closed: a failed enable is a failed apply.
hermes plugins enable security-guidance
hermes plugins enable web/ddgs

echo "WORKFLOW_APPLY_COMPLETED plan=$PLAN_FILE"
echo "Configure credentials with Hermes official auth/model commands."
echo "Restart Hermes or use /reset before verifying skills/tools."

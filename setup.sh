#!/bin/bash
# Thin Workflow-assistance installer. Hermes Agent itself must already exist.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
if [ -z "${HERMES_HOME:-}" ]; then
    case "$(uname -s 2>/dev/null || echo unknown)" in
        MINGW*|MSYS*|CYGWIN*) HERMES_HOME="${LOCALAPPDATA:-$HOME/AppData/Local}/hermes" ;;
        *) HERMES_HOME="$HOME/.hermes" ;;
    esac
fi

command -v hermes >/dev/null || { echo "Hermes Agent is not installed" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
mkdir -p "$HERMES_HOME"

python3 "$REPO_ROOT/scripts/workflow/sync_hermes_workflow_assets.py" \
    --repo "$REPO_ROOT" --home "$HERMES_HOME" --apply

# Keep portable defaults minimal. Optional media/X/Spotify/meeting tools stay opt-in.
hermes plugins enable security-guidance 2>/dev/null || true
hermes plugins enable web/ddgs 2>/dev/null || true

echo "Workflow assets deployed. Configure credentials with Hermes official auth/model commands."
echo "Restart Hermes or use /reset before verifying skills/tools."

<#
.SYNOPSIS
    Thin Workflow-assistance installer. Hermes Agent must already be installed.
.DESCRIPTION
    Calls the canonical repo-to-live sync script. It preserves an existing live
    provider/model and never copies credentials or runtime state.
#>
param(
    [string]$HermesHome = "$env:LOCALAPPDATA\hermes"
)

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot

if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) {
    throw "Hermes Agent is not installed or not in PATH"
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is required"
}
if (-not (Test-Path $HermesHome)) {
    New-Item -ItemType Directory -Path $HermesHome -Force | Out-Null
}

$SyncScript = Join-Path $RepoRoot "scripts\workflow\sync_hermes_workflow_assets.py"
& python $SyncScript --repo $RepoRoot --home $HermesHome --apply
if ($LASTEXITCODE -ne 0) {
    throw "Workflow asset sync failed with exit code $LASTEXITCODE"
}

& hermes plugins enable security-guidance 2>&1 | Out-Null
& hermes plugins enable web/ddgs 2>&1 | Out-Null

Write-Host "Workflow assets deployed. Configure credentials with Hermes official auth/model commands."
Write-Host "Restart Hermes or use /reset before verifying skills/tools."

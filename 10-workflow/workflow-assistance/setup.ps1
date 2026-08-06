<#
.SYNOPSIS
    Plan-first Workflow-assistance installer. Hermes Agent must already be installed for apply.
.DESCRIPTION
    By default, generates a project-local ActionPlan and performs no live write.
    Only an explicit -Apply switch executes the approved repo-to-live sync. The
    script never copies credentials or runtime state and fails closed on plugin errors.
#>
param(
    [string]$HermesHome = "$env:LOCALAPPDATA\hermes",
    [switch]$Apply,
    [string]$PlanFile = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($PlanFile)) {
    $PlanFile = Join-Path $RepoRoot ".hermes\task-artifacts\setup-plan.json"
}

$PythonCommandInfo = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCommandInfo) {
    $PythonCommandInfo = Get-Command py -ErrorAction SilentlyContinue
    if (-not $PythonCommandInfo) {
        throw "A working Python interpreter is required"
    }
    $PythonCommand = $PythonCommandInfo.Source
    $PythonPrefixArgs = @("-3")
} else {
    $PythonCommand = $PythonCommandInfo.Source
    $PythonPrefixArgs = @()
}
$PythonVersion = & $PythonCommand @PythonPrefixArgs --version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Python interpreter could not be executed: $PythonCommand"
}
if (-not (Test-Path -LiteralPath $HermesHome -PathType Container)) {
    throw "Hermes home must already exist; refusing to create a live target: $HermesHome"
}

$SyncScript = Join-Path $RepoRoot "scripts\workflow\sync_hermes_workflow_assets.py"
$SyncArgs = @(
    $SyncScript,
    "--repo", $RepoRoot,
    "--home", $HermesHome,
    "--plan-json", $PlanFile
)
if ($Apply) {
    if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) {
        throw "Hermes Agent is required for --Apply plugin readback and is not in PATH"
    }
    $SyncArgs += @("--apply", "--approved")
}

& $PythonCommand @PythonPrefixArgs @SyncArgs
if ($LASTEXITCODE -ne 0) {
    throw "Workflow asset sync failed with exit code $LASTEXITCODE"
}

if (-not $Apply) {
    Write-Host "ACTION_PLAN_ONLY path=$PlanFile"
    Write-Host "No live files or plugins were changed. Review the plan, then rerun with -Apply."
    exit 0
}

foreach ($Plugin in @("security-guidance", "web/ddgs")) {
    & hermes plugins enable $Plugin
    if ($LASTEXITCODE -ne 0) {
        throw "Required plugin enable failed: $Plugin (exit code $LASTEXITCODE)"
    }
}

Write-Host "WORKFLOW_APPLY_COMPLETED plan=$PlanFile"
Write-Host "Configure credentials with Hermes official auth/model commands."
Write-Host "Restart Hermes or use /reset before verifying skills/tools."

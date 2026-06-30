<#
.SYNOPSIS
    Hermes Agent one-click deployment script
.DESCRIPTION
    Auto-deploy Hermes Agent on a new machine:
    - Install Hermes Agent
    - Copy config.yaml / SOUL.md / .env.template
    - Install local skills
    - Install ddgs dependency
    - Enable toolsets & plugins
.NOTES
    Run from repo root (or use setup.sh via git-bash on Windows).
    After deployment, fill in API keys in .env.
    If encoding errors occur, use setup.sh instead.
#>

param(
    [switch]$DryRun,
    [string]$HermesHome = "$env:LOCALAPPDATA\hermes"
)

$ErrorActionPreference = "Stop"
# Repo root is the directory containing this script.
# Keep this path calculation simple so a freshly cloned repo works on any machine.
$RepoRoot = $PSScriptRoot
$PackDir = $RepoRoot

function Write-Step {
    param([string]$Message, [string]$Status = "[...]")
    Write-Host "`n$Status $Message" -ForegroundColor Cyan
}

function Invoke-Command {
    param([string]$Command)
    if ($DryRun) {
        Write-Host "  [DRY-RUN] $Command" -ForegroundColor Yellow
        return
    }
    Write-Host "  > $Command" -ForegroundColor Gray
    Invoke-Expression $Command 2>&1 | Out-Host
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        throw "Command failed (exit $LASTEXITCODE): $Command"
    }
}

# ==== Step 0: System Check ====
Write-Step "System environment check"

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "  [WARN] winget not found, skipping package manager install"
    $HasWinget = $false
} else {
    Write-Host "  [OK] winget available"
    $HasWinget = $true
}

# ==== Step 1: Install Hermes Agent ====
Write-Step "Step 1: Install Hermes Agent"

Invoke-Command 'winget install NousResearch.HermesAgent 2>$null'
if ($LASTEXITCODE -ne 0) {
    Write-Host "  winget source not found, trying pip install..."
    Invoke-Command 'pip install hermes-agent'
}

# ==== Step 2: Verify Installation ====
Write-Step "Step 2: Verify installation"

$hermesCmd = Get-Command hermes -ErrorAction SilentlyContinue
if (-not $hermesCmd) {
    $hermesExe = "$env:LOCALAPPDATA\hermes\.venv\Scripts\hermes.exe"
    if (Test-Path $hermesExe) {
        Write-Host "  [OK] Hermes found at: $hermesExe"
        $script:hermesExe = $hermesExe
    } else {
        Write-Warning "  [FAIL] Hermes not found. Restart terminal and try again."
        return
    }
} else {
    Write-Host "  [OK] Hermes found in PATH: $($hermesCmd.Source)"
    $script:hermesExe = "hermes"
}

# ==== Step 3: Configure Hermes ====
Write-Step "Step 3: Write config files"

if (-not (Test-Path $HermesHome)) {
    New-Item -ItemType Directory -Path $HermesHome -Force | Out-Null
}

$configSrc = Join-Path $PackDir "config" "config.yaml"
$configDst = Join-Path $HermesHome "config.yaml"
if (Test-Path $configSrc) {
    Copy-Item -Path $configSrc -Destination $configDst -Force
    Write-Host "  [OK] config.yaml copied"
}

$soulSrc = Join-Path $PackDir "config" "SOUL.md"
$soulDst = Join-Path $HermesHome "SOUL.md"
if (Test-Path $soulSrc) {
    Copy-Item -Path $soulSrc -Destination $soulDst -Force
    Write-Host "  [OK] SOUL.md copied"
}

$envSrc = Join-Path $PackDir "config" ".env.template"
$envDst = Join-Path $HermesHome ".env"
if ((Test-Path $envSrc) -and -not (Test-Path $envDst)) {
    Copy-Item -Path $envSrc -Destination $envDst -Force
    Write-Host "  [OK] .env template created (fill in API keys)"
} elseif (Test-Path $envDst) {
    Write-Host "  [OK] .env exists, keeping current config"
}

# ==== Step 4: Install Skills ====
Write-Step "Step 4: Install local skills"

$skillsSrc = Join-Path $PackDir "skills"
$skillsDst = Join-Path $HermesHome "skills"

if (Test-Path $skillsSrc) {
    if (-not (Test-Path $skillsDst)) {
        New-Item -ItemType Directory -Path $skillsDst -Force | Out-Null
    }

    Get-ChildItem -Path $skillsSrc -Recurse -Directory | ForEach-Object {
        $relPath = $_.FullName.Substring($skillsSrc.Length + 1)
        $targetDir = Join-Path $skillsDst $relPath
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
    }
    Get-ChildItem -Path $skillsSrc -Recurse -File | ForEach-Object {
        $relPath = $_.FullName.Substring($skillsSrc.Length + 1)
        $targetPath = Join-Path $skillsDst $relPath
        Copy-Item -Path $_.FullName -Destination $targetPath -Force
    }
    Write-Host "  [OK] Skills installed to $skillsDst"
}

# ==== Step 5: Install ddgs ====
Write-Step "Step 5: Install Python dependency (ddgs)"

$hermesPip = Join-Path $HermesHome ".venv" "Scripts" "pip.exe"
if (Test-Path $hermesPip) {
    & $hermesPip install ddgs 2>&1 | Out-Null
    Write-Host "  [OK] ddgs installed (DuckDuckGo search)"
}

# ==== Step 6: Enable toolsets & plugins ====
Write-Step "Step 6: Enable toolsets & plugins"

& $script:hermesExe tools enable x_search 2>&1 | Out-Null
& $script:hermesExe tools enable video 2>&1 | Out-Null
& $script:hermesExe tools enable spotify 2>&1 | Out-Null
& $script:hermesExe plugins enable disk-cleanup 2>&1 | Out-Null
& $script:hermesExe plugins enable google_meet 2>&1 | Out-Null
& $script:hermesExe plugins enable security-guidance 2>&1 | Out-Null
& $script:hermesExe plugins enable spotify 2>&1 | Out-Null
& $script:hermesExe plugins enable web/ddgs 2>&1 | Out-Null

Write-Host "  [OK] Toolsets and plugins enabled"

# ==== Done ====
Write-Step "Deployment complete" "DONE"
Write-Host ""
Write-Host "Manual steps remaining:" -ForegroundColor Yellow
Write-Host "  1. API Key: set DEEPSEEK_API_KEY in $HermesHome\.env" -ForegroundColor White
Write-Host "  2. Model: run 'hermes model' to select provider/model" -ForegroundColor White
Write-Host "  3. (Optional) Spotify: run 'hermes auth spotify'" -ForegroundColor White
Write-Host "  4. Restart Hermes for plugins to take effect" -ForegroundColor White
Write-Host ""
Write-Host "To load skills (auto on new session):" -ForegroundColor Green
Write-Host "  hermes -s screenlingua" -ForegroundColor Green
Write-Host "  See README.md for details" -ForegroundColor Gray

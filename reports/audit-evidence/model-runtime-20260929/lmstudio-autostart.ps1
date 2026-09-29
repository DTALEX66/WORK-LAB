<#
  WORK-LAB local AI runtime: bring LM Studio up and preload the FAST lane.

  Purpose: the user does not drive the LM Studio GUI. After a reboot the inference
  server must come back on its own and the interactive lane must be warm, so any
  caller (ArcheAxis, WORK-LAB, DESIGN-LAB) just works.

  Behaviour:
    1. Wait for LM Studio's inference server to answer on 127.0.0.1:1234.
       If it is not up, try `lms server start` once.
    2. Preload the FAST model with a long TTL so it stays resident.
    3. Do NOT preload DEEP or the VLM: they are large and load just-in-time in
       about 17 s and about 5 s respectively, which is far better than holding
       VRAM permanently on an 8 GiB card.
    4. Everything is appended to a log so a later run can be audited.

  Idempotent: safe to run repeatedly. Exit code 0 means the endpoint is serving.
#>
[CmdletBinding()]
param(
  [int]$FastContextLength = 8192,
  [int]$FastTtlSeconds    = 86400,
  [int]$FastParallel      = 1,
  [int]$WaitForServerSec  = 180,
  # -Heal: run periodically. If the server is down, relaunch LM Studio (which
  # brings the server up because autoStartOnLaunch is enabled) and preload FAST.
  # Without -Heal this is the logon warm-up.
  [switch]$Heal
)

$ErrorActionPreference = 'Continue'
$ProgressPreference    = 'SilentlyContinue'

$Base       = 'http://127.0.0.1:1234'
$Lms        = Join-Path $env:USERPROFILE '.lmstudio\bin\lms.exe'
$LogDir     = Join-Path $env:LOCALAPPDATA 'WORK-LAB\logs'
$LogFile    = Join-Path $LogDir 'lmstudio-autostart.log'
$FastModel  = 'qwen3.5-4b'
$Gui        = Join-Path $env:LOCALAPPDATA 'Programs\LM Studio\LM Studio.exe'

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Keep the log bounded: it is appended to every 10 minutes in heal mode.
if ((Test-Path $LogFile) -and ((Get-Item $LogFile).Length -gt 1MB)) {
  Move-Item -Force $LogFile "$LogFile.1"
}

function Write-Log([string]$Message) {
  $line = '{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
  Add-Content -Path $LogFile -Value $line -Encoding utf8
  if (-not $Heal) { Write-Host $line }
}

function Test-Server {
  try {
    $r = Invoke-WebRequest -Uri "$Base/v1/models" -UseBasicParsing -TimeoutSec 5
    return ($r.StatusCode -eq 200)
  } catch { return $false }
}

function Ensure-Gui {
  $procs = Get-Process -Name 'LM Studio' -ErrorAction SilentlyContinue
  if ($procs) { return 'already running' }
  if (-not (Test-Path $Gui)) { return "GUI not found at $Gui" }
  Start-Process -FilePath $Gui | Out-Null
  return 'launched'
}

$quiet = $Heal -and (Test-Server)

if (-not $quiet) {
  Write-Log $(if ($Heal) { '--- heal check begin ---' } else { '--- lmstudio-autostart begin ---' })
}

# 1. wait for the server, nudging it as needed
$deadline = (Get-Date).AddSeconds($WaitForServerSec)
$nudgedGui = $false
$nudgedCli = $false
while ((Get-Date) -lt $deadline) {
  if (Test-Server) { break }
  if (-not $nudgedGui) {
    $how = Ensure-Gui
    if (-not $quiet) { Write-Log "LM Studio GUI: $how" }
    $nudgedGui = $true
    if ($how -eq 'launched') { Start-Sleep -Seconds 15 }
  }
  if (-not (Test-Server) -and -not $nudgedCli) {
    if (-not $quiet) { Write-Log 'server still down; attempting: lms server start' }
    try { & $Lms server start 2>&1 | ForEach-Object { if (-not $quiet) { Write-Log "  $_" } } }
    catch { if (-not $quiet) { Write-Log "  lms server start failed: $($_.Exception.Message)" } }
    $nudgedCli = $true
  }
  Start-Sleep -Seconds 5
}

if (-not (Test-Server)) {
  Write-Log 'FAILED: inference server is not answering after remediation attempts'
  exit 1
}
if (-not $quiet) { Write-Log 'inference server is answering on 1234' }

# 2. bring the FAST lane to exactly one resident instance
#
# Each `lms load` of an already-loaded model creates ANOTHER instance
# (qwen3.5-4b, then qwen3.5-4b:2, ...). A check that merely looks for the model
# name therefore cannot see duplicates, and each duplicate holds real VRAM. So the
# JSON view is used to count exact identifiers, extras are unloaded, and only a
# genuinely absent model is loaded (with --parallel 1: one extra prediction slot
# per instance wastes memory on an 8 GiB card for a single-user desktop).
if (-not (Test-Path $Lms)) {
  Write-Log "WARNING: lms CLI missing at $Lms; skipping preload"
  exit 0
}

function Get-LoadedFast([string]$BaseName) {
  try {
    $raw = & $Lms ps --json 2>$null
    $text = ($raw | Out-String).Trim()
    if (-not $text) { return @() }
    $items = @($text | ConvertFrom-Json)
  } catch {
    return @()
  }
  # exact identifier match, or an instance suffix like ":2" - never a fuzzy name hit
  return @($items | Where-Object {
    $_.identifier -and (
      $_.identifier -eq $BaseName -or $_.identifier -like "$BaseName`:*"
    )
  })
}

$instances = Get-LoadedFast $FastModel
$names = @($instances | ForEach-Object { $_.identifier })
if ($names.Count -eq 0) {
  Write-Log "preloading FAST: $FastModel (ctx=$FastContextLength ttl=$FastTtlSeconds parallel=$FastParallel)"
  $out = & $Lms load $FastModel --context-length $FastContextLength --ttl $FastTtlSeconds --parallel $FastParallel -y 2>&1 | Out-String
  foreach ($line in ($out -split "`r?`n" | Where-Object { $_ -and $_ -notmatch '^\s*$' } | Select-Object -Last 3)) {
    Write-Log "  $line"
  }
} elseif ($names.Count -eq 1) {
  if (-not $quiet) { Write-Log "FAST already loaded: $($names[0])" }
} else {
  Write-Log "duplicate FAST instances detected: $($names -join ', ') - removing all but the first"
  foreach ($extra in ($names | Select-Object -Skip 1)) {
    & $Lms unload $extra 2>&1 | ForEach-Object { Write-Log "  unload $extra -> $_" }
  }
}

if (-not $quiet) {
  Write-Log $(if ($Heal) { '--- heal check end ---' } else { '--- lmstudio-autostart end ---' })
}
exit 0

# Register both WORK-LAB LM Studio scheduled tasks.
#
#   1. "WORK-LAB LM Studio warm-up"  - at logon (+90 s): make the server answer and
#      preload the FAST lane.
#   2. "WORK-LAB LM Studio health"   - every 10 minutes: if the server is down,
#      relaunch LM Studio and preload FAST again.
#
# Task 2 exists because the user does not operate LM Studio: if the app crashes or
# is closed, nobody would notice and every model consumer would fail silently.
# Verified by actually killing LM Studio and observing recovery.
#
# The periodic task runs through a wrapper script (lmstudio-heal.ps1) so that the
# task's /TR contains only a bare path: schtasks mangles quoted arguments that
# follow -File and mistakes "-Heal" for one of its own switches.
#
# Safe to run repeatedly: existing tasks are replaced.

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

$WarmScript = Join-Path $env:LOCALAPPDATA 'WORK-LAB\lmstudio-autostart.ps1'
$HealScript = Join-Path $env:LOCALAPPDATA 'WORK-LAB\lmstudio-heal.ps1'
$LogDir     = Join-Path $env:LOCALAPPDATA 'WORK-LAB\logs'
$Pwsh       = 'C:\Program Files\PowerShell\7\pwsh.exe'
if (-not (Test-Path $Pwsh)) {
  $Pwsh = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
}
$Schtasks = Join-Path $env:SystemRoot 'System32\schtasks.exe'

foreach ($f in $WarmScript, $HealScript) {
  if (-not (Test-Path $f)) { throw "missing required script: $f" }
}
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$WarmName = 'WORK-LAB LM Studio warm-up'
$HealName = 'WORK-LAB LM Studio health'

Write-Host "warm-up script : $WarmScript"
Write-Host "health  script : $HealScript"
Write-Host "shell          : $Pwsh"
Write-Host ''

# ---- 1. logon warm-up -------------------------------------------------------
$action = New-ScheduledTaskAction -Execute $Pwsh `
  -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $WarmScript)
$logon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$logon.Delay = 'PT90S'
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries -StartWhenAvailable `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
  -LogonType Interactive -RunLevel Limited

if (Get-ScheduledTask -TaskName $WarmName -ErrorAction SilentlyContinue) {
  Write-Host "replacing: $WarmName"
  Unregister-ScheduledTask -TaskName $WarmName -Confirm:$false
}
Register-ScheduledTask -TaskName $WarmName -Action $action -Trigger $logon `
  -Settings $settings -Principal $principal `
  -Description 'Brings the LM Studio inference server up at logon and preloads the FAST lane so local model providers work without the user opening LM Studio.' | Out-Null
Write-Host "registered: $WarmName"

# ---- 2. periodic health check ----------------------------------------------
if (Get-ScheduledTask -TaskName $HealName -ErrorAction SilentlyContinue) {
  Write-Host "replacing: $HealName"
  Unregister-ScheduledTask -TaskName $HealName -Confirm:$false
}
$tr = '"{0}" -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{1}"' -f $Pwsh, $HealScript
& $Schtasks /Create /TN $HealName /SC MINUTE /MO 10 /TR $tr /F | Out-String | Write-Host
Write-Host "registered: $HealName (every 10 minutes)"

Write-Host ''
Write-Host '=== registered tasks ==='
foreach ($n in $WarmName, $HealName) {
  $t = Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue
  if (-not $t) { Write-Host "  $n : MISSING"; continue }
  Write-Host "  $n"
  Write-Host "      state   : $($t.State)"
  Write-Host "      action  : $($t.Actions[0].Execute)"
  Write-Host "      args    : $($t.Actions[0].Arguments)"
  $shown = $false
  foreach ($trig in $t.Triggers) {
    $rep = $trig.Repetition
    if ($rep -and $rep.Interval -and $rep.Interval -ne 'PT0S') {
      Write-Host "      trigger : repeats every $($rep.Interval)"; $shown = $true
    }
    if ($trig.Delay) { Write-Host "      trigger : AtLogOn + $($trig.Delay)"; $shown = $true }
  }
  if (-not $shown) { Write-Host '      trigger : (see schtasks /Query /TN)' }
}

Write-Host ''
Write-Host '=== triggering the health task now to verify ==='
Start-ScheduledTask -TaskName $HealName
Start-Sleep -Seconds 15
$info = Get-ScheduledTaskInfo -TaskName $HealName
Write-Host "  LastRunTime   : $($info.LastRunTime)"
Write-Host "  LastTaskResult: $($info.LastTaskResult)  (0 = success)"

try {
  $r = Invoke-WebRequest -Uri 'http://127.0.0.1:1234/v1/models' -UseBasicParsing -TimeoutSec 10
  $ids = (($r.Content | ConvertFrom-Json).data).id
  Write-Host "  endpoint      : HTTP $($r.StatusCode)"
  Write-Host "  models        : $($ids.Count) indexed"
} catch {
  Write-Host '  endpoint      : UNREACHABLE'
}

Write-Host ''
Write-Host '=== schtasks view ==='
& $Schtasks /Query /TN $HealName /FO LIST | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" }

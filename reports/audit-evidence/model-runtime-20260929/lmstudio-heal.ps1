# Wrapper for the periodic WORK-LAB LM Studio health task.
#
# Kept separate so that the scheduled task's command line contains nothing but a
# simple script path: schtasks /TR mangles quoted arguments that follow -File and
# treats "-Heal" as one of its own options.
#
# Runs the autostart script in heal mode and appends its output, so a failure is
# discoverable even though the scheduled task runs with no visible window.

$Script = Join-Path $env:LOCALAPPDATA 'WORK-LAB\lmstudio-autostart.ps1'
$LogDir = Join-Path $env:LOCALAPPDATA 'WORK-LAB\logs'
$Out    = Join-Path $LogDir 'lmstudio-heal-wrapper.log'

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if ((Test-Path $Out) -and ((Get-Item $Out).Length -gt 512KB)) {
  Move-Item -Force $Out "$Out.1"
}

& $Script -Heal *>> $Out
exit $LASTEXITCODE

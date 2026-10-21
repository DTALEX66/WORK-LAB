@echo off
title WORK-LAB Observer - Read-only dashboard
echo ============================================
echo   WORK-LAB Observer - One-click start
echo   (read-only: loopback sidecar + static UI)
echo ============================================
echo.

rem The legacy observability stack (Grafana/Phoenix/Prometheus/Loki under
rem .hermes\task-runtime\agent-observability) and the standalone
rem observer_live_server.py were RETIRED (NF-09): the former was deleted in
rem the R4 cleanup, the latter fabricated LIVE/git state and read private
rem DBs by default. This launcher now starts the canonical read-only chain:
rem the Workflow-owned loopback sidecar + the static web frontend.
rem
rem 2026-10-19 (standalone run): this file used to open a static HTML path under
rem an observer directory that does not exist in the repository, while polling a
rem hardcoded port 61867 that the sidecar never binds (it starts with --port 0,
rem i.e. a random free port). The documented one-click chain therefore could not
rem come up at all. It now serves the built Vite bundle from the sidecar's own
rem --frontend-root and opens the URL that the sidecar's endpoint descriptor
rem advertises, so no port is guessed and the UI's injected endpoint stays a
rem loopback /api/v1 URL.

set "ROOT=%~dp0..\.."
set "RUNTIME=%ROOT%\.project-local\runs\workflow"
set "DESCRIPTOR=%RUNTIME%\sidecar-endpoint.json"
set "LAUNCH_FILE=%DESCRIPTOR%.launch"

rem A descriptor left by an earlier run advertises a port that is already gone.
if exist "%DESCRIPTOR%" del /q "%DESCRIPTOR%"
if exist "%LAUNCH_FILE%" del /q "%LAUNCH_FILE%"

echo 1. Starting loopback sidecar (snapshot + events SSE + the static UI)...
start "work-lab-sidecar" cmd /c "python "%ROOT%\services\orchestration\sidecar.py" --project-root "%ROOT%" --runtime-root "%RUNTIME%" --host 127.0.0.1 --port 0 --frontend-root "%ROOT%\apps\observer\frontend\dist""

echo 2. Waiting for the endpoint descriptor (the descriptor decides the port, not a guess)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline=(Get-Date).AddSeconds(25); $path='%DESCRIPTOR%'; $url=''; while ((Get-Date) -lt $deadline) { if (Test-Path -LiteralPath $path) { try { $d = ConvertFrom-Json -InputObject (Get-Content -Raw -LiteralPath $path); if ($d.projectionUrl) { $url = [string]$d.projectionUrl; break } } catch { } }; Start-Sleep -Milliseconds 400 }; if ($url -ne '') { $ui = $url.Replace('/api/v1/snapshot',''); Set-Content -LiteralPath '%LAUNCH_FILE%' -Value ($ui + '/?api=' + $url + '&view=full&theme=dark') -Encoding ascii } else { Write-Host 'SIDECAR_DESCRIPTOR_MISSING' }"

if not exist "%LAUNCH_FILE%" (
  echo The sidecar never advertised an endpoint, so nothing was opened.
  echo Start it by hand and read the WORKFLOW_SIDECAR_READY line:
  echo   python services/orchestration/sidecar.py --project-root . --runtime-root "%RUNTIME%" --frontend-root "%ROOT%\apps\observer\frontend\dist"
  echo.
  pause
  exit /b 1
)

set /p LAUNCH_URL=<"%LAUNCH_FILE%"
echo 3. Opening the Observer UI the sidecar serves...
echo    %LAUNCH_URL%
start "" "%LAUNCH_URL%"

echo.
echo The dashboard projects the loopback snapshot only. If it cannot reach the sidecar it
echo shows OFFLINE/UNKNOWN truthfully - it never fakes LIVE.
echo The packaged desktop entry is still the Tauri Observer; this launcher is the
echo standalone loopback chain for this repository.
echo.
pause

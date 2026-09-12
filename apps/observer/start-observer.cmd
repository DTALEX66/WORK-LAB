@echo off
title WORK-LAB Observer - Read-only dashboard
echo ============================================
echo   WORK-LAB Observer - One-click start
echo   (read-only: sidecar + static frontend)
echo ============================================
echo.

rem The legacy observability stack (Grafana/Phoenix/Prometheus/Loki under
rem .hermes\task-runtime\agent-observability) and the standalone
rem observer_live_server.py were RETIRED (NF-09): the former was deleted in
rem the R4 cleanup, the latter fabricated LIVE/git state and read private
rem DBs by default. This launcher now starts the canonical read-only chain:
rem the Workflow-owned loopback sidecar + the static web frontend.

set "ROOT=%~dp0..\.."

echo 1. Starting loopback sidecar (snapshot + events SSE)...
start "work-lab-sidecar" cmd /c "python "%ROOT%\services\orchestration\sidecar.py" --project-root "%ROOT%" --runtime-root "%ROOT%\.project-local\runs\workflow""

echo 2. Waiting for the snapshot endpoint...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$deadline = (Get-Date).AddSeconds(20); $ok = $false; while ((Get-Date) -lt $deadline) { try { $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:61867/api/v1/snapshot' -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ok = $true; break } } catch { Start-Sleep -Milliseconds 500 } }; if (-not $ok) { Write-Host 'sidecar did not become ready in 20s; open the UI anyway - it will show OFFLINE/UNKNOWN truthfully' }"

echo 3. Opening Observer (static frontend served from web/)...
start "" "%ROOT%\apps\observer\web\index.html?view=full&theme=dark"

echo.
echo Observer frontend: apps\observer\web (queries http://127.0.0.1:61867/api/v1/snapshot)
echo If the sidecar is down the dashboard shows OFFLINE truthfully - it never fakes LIVE.
echo.
pause

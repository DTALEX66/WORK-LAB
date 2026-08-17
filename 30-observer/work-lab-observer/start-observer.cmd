@echo off
title WORK-LAB Observer - Control Tower
echo ============================================
echo   WORK-LAB Observer - One-click start
echo   Frontend: OB interface / Backend: WORK-LAB
echo ============================================
echo.
rem 1. Start observability backend stack (Grafana/Phoenix/Prometheus/Loki/OTEL/metrics)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\..\.hermes\task-runtime\agent-observability\start-services.ps1"
echo.
echo 2. Start sidecar API (snapshot source for OB interface)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\..\.hermes\task-runtime\agent-observability\start-sidecar.ps1"
echo.
echo 3. Waiting for services...
timeout /t 15 /nobreak >nul
echo 4. Opening OB interface...
start "" "http://127.0.0.1:8089/index.html?view=full&theme=dark&api=http%3A%2F%2F127.0.0.1%3A61867%2Fapi%2Fv1%2Fsnapshot"
echo.
echo Done. OB interface: http://127.0.0.1:8089
echo Backend: Grafana(:3000) Phoenix(:6006) Prometheus(:9090) Loki(:3100)
echo.
pause

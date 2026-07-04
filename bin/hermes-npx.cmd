@echo off
setlocal EnableExtensions EnableDelayedExpansion
if "%HERMES_HOME%"=="" set "HERMES_HOME=%LOCALAPPDATA%\hermes"
if exist "%HERMES_HOME%\node\npx.cmd" (
  "%HERMES_HOME%\node\npx.cmd" %*
  exit /b %ERRORLEVEL%
)
set "NODE_MAJOR=0"
for /f "usebackq delims=" %%v in (`node -p "process.versions.node.split('.')[0]" 2^>nul`) do set "NODE_MAJOR=%%v"
if !NODE_MAJOR! GEQ 20 (
  where npx >nul 2>nul
  if !ERRORLEVEL! EQU 0 (
    npx %*
    exit /b !ERRORLEVEL!
  )
)
echo hermes-npx: Hermes bundled npx not found. Install Hermes bundled Node or set HERMES_HOME. 1>&2
echo PATH fallback requires trusted Node ^>=20 and npx in PATH. 1>&2
exit /b 127

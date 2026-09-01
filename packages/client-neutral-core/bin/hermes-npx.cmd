@echo off
setlocal EnableExtensions EnableDelayedExpansion
if "%HERMES_HOME%"=="" set "HERMES_HOME=%LOCALAPPDATA%\hermes"
if exist "%HERMES_HOME%\node\npx.cmd" (
  rem npx starts its package via `env node`; make the Hermes-owned runtime
  rem win over unrelated Node installations earlier on the global PATH.
  set "PATH=%HERMES_HOME%\node;%PATH%"
  "%HERMES_HOME%\node\npx.cmd" %*
  exit /b %ERRORLEVEL%
)
if "%HERMES_NPX_ALLOW_PATH_FALLBACK%"=="1" (
  set "NODE_MAJOR=0"
  for /f "usebackq delims=" %%v in (`node -p "process.versions.node.split('.')[0]" 2^>nul`) do set "NODE_MAJOR=%%v"
  if !NODE_MAJOR! GEQ 20 (
    where npx >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
      npx %*
      exit /b !ERRORLEVEL!
    )
  )
  echo hermes-npx: PATH fallback requested but trusted Node ^>=20 or npx not found. 1>&2
  exit /b 127
)
echo hermes-npx: Hermes bundled npx not found. Install Hermes bundled Node or set HERMES_HOME. 1>&2
echo Set HERMES_NPX_ALLOW_PATH_FALLBACK=1 only if PATH Node is trusted and ^>=20. 1>&2
exit /b 127

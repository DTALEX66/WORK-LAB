@echo off
setlocal
if "%HERMES_HOME%"=="" set "HERMES_HOME=%LOCALAPPDATA%\hermes"
if exist "%HERMES_HOME%\node\npx.cmd" (
  "%HERMES_HOME%\node\npx.cmd" %*
  exit /b %ERRORLEVEL%
)
where npx >nul 2>nul
if %ERRORLEVEL%==0 (
  npx %*
  exit /b %ERRORLEVEL%
)
echo hermes-npx: npx not found. Install Node.js or Hermes bundled node. 1>&2
exit /b 127

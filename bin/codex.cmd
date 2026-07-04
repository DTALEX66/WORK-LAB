@echo off
setlocal EnableExtensions

rem Portable Codex CLI launcher for Workflow-assistance.
rem It does not bundle Codex or credentials; it only locates an already-installed Codex binary.

if not "%CODEX_CLI%"=="" if exist "%CODEX_CLI%" (
  "%CODEX_CLI%" %*
  exit /b %ERRORLEVEL%
)

set "CODEX_CANDIDATE=%USERPROFILE%\.codex\plugins\.plugin-appserver\codex.exe"
if exist "%CODEX_CANDIDATE%" (
  "%CODEX_CANDIDATE%" %*
  exit /b %ERRORLEVEL%
)

set "CODEX_CANDIDATE=%LOCALAPPDATA%\OpenAI\Codex\bin\codex.exe"
if exist "%CODEX_CANDIDATE%" (
  "%CODEX_CANDIDATE%" %*
  exit /b %ERRORLEVEL%
)

for /f "usebackq delims=" %%i in (`where codex.exe 2^>nul`) do (
  "%%i" %*
  exit /b %ERRORLEVEL%
)

echo codex wrapper: Codex CLI not found. 1>&2
echo Install/login Codex first, or set CODEX_CLI to the Codex executable path. 1>&2
exit /b 127

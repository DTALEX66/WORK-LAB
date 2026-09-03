@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Portable Codex CLI launcher for Workflow-assistance.
rem Windows Store OpenAI.Codex owns the runtime. The plugin copy is executable
rem only when its SHA-256 is identical to the current Store codex.exe.

if not "%CODEX_CLI%"=="" if exist "%CODEX_CLI%" (
  "%CODEX_CLI%" %*
  exit /b %ERRORLEVEL%
)

powershell.exe -NoProfile -Command "$p=(Get-AppxPackage -Name OpenAI.Codex)[0]; if(-not $p){exit 2}; $store=Join-Path $p.InstallLocation 'app\resources\codex.exe'; $plugin=Join-Path $env:USERPROFILE '.codex\plugins\.plugin-appserver\codex.exe'; if(-not (Test-Path -LiteralPath $store)){exit 3}; if(-not (Test-Path -LiteralPath $plugin)){exit 4}; if((Get-FileHash -LiteralPath $store -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $plugin -Algorithm SHA256).Hash){exit 78}; exit 0"
if not errorlevel 1 (
  set "CODEX_CANDIDATE=%USERPROFILE%\\.codex\\plugins\\.plugin-appserver\\codex.exe"
  if exist "!CODEX_CANDIDATE!" (
    "!CODEX_CANDIDATE!" %*
    exit /b %ERRORLEVEL%
  )
) else (
  if errorlevel 78 (
    echo codex wrapper: Store and executable bridge differ; refusing runtime drift. 1>&2
    exit /b 78
  )
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

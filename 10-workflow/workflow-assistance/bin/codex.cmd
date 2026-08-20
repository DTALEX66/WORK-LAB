@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Codex CLI launcher for Workflow-assistance.
rem 2026-08-20: switched from Windows Store OpenAI.Codex to official Git CLI
rem (npm @openai/codex). Same ~/.codex CODEX_HOME: sessions, config, auth all
rem shared - nothing lost. Override with CODEX_CLI env var when needed.

if not "%CODEX_CLI%"=="" if exist "%CODEX_CLI%" (
  "%CODEX_CLI%" %*
  exit /b %ERRORLEVEL%
)

set "NPM_ROOT=C:\Users\ALEX\AppData\Local\hermes\node"
if exist "%NPM_ROOT%\node_modules\@openai\codex\bin\codex.js" (
  "%NPM_ROOT%\node.exe" "%NPM_ROOT%\node_modules\@openai\codex\bin\codex.js" %*
  exit /b %ERRORLEVEL%
)

rem fallback: legacy store runtime (hash-verified) if npm CLI missing
powershell.exe -NoProfile -Command "$p=(Get-AppxPackage -Name OpenAI.Codex)[0]; if(-not $p){exit 2}; $store=Join-Path $p.InstallLocation 'app\resources\codex.exe'; $plugin=Join-Path $env:USERPROFILE '.codex\plugins\.plugin-appserver\codex.exe'; if(-not (Test-Path -LiteralPath $store)){exit 3}; if(-not (Test-Path -LiteralPath $plugin)){exit 4}; if((Get-FileHash -LiteralPath $store -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $plugin -Algorithm SHA256).Hash){exit 78}; exit 0"
if not errorlevel 1 (
  set "CODEX_CANDIDATE=%USERPROFILE%\.codex\plugins\.plugin-appserver\codex.exe"
  if exist "%CODEX_CANDIDATE%" (
    "%CODEX_CANDIDATE%" %*
    exit /b %ERRORLEVEL%
  )
)
exit /b 127

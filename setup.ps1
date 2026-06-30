<#
.SYNOPSIS
    Hermes Agent 一键部署脚本
.DESCRIPTION
    在新电脑上自动部署 Hermes Agent 及全套配置：
    - 安装 Hermes Agent
    - 复制 config.yaml / SOUL.md / .env.template
    - 安装本地技能
    - 安装额外 Python 依赖 (ddgs)
.NOTES
    需要管理员权限运行（用于安装 winget 包等）
    部署后需在 .env 中填入 API Key（见部署后步骤）
#>

param(
    [switch]$DryRun,
    [string]$HermesHome = "$env:LOCALAPPDATA\hermes"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$PackDir = $RepoRoot

function Write-Step {
    param([string]$Message, [string]$Status = "⏳")
    Write-Host "`n$Status $Message" -ForegroundColor Cyan
}

function Invoke-Command {
    param([string]$Command)
    if ($DryRun) {
        Write-Host "  [DRY-RUN] $Command" -ForegroundColor Yellow
        return
    }
    Write-Host "  > $Command" -ForegroundColor Gray
    Invoke-Expression $Command 2>&1 | Out-Host
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE: $Command"
    }
}

# ═══════════════════════════════════════════════
# Step 0: System Check
# ═══════════════════════════════════════════════
Write-Step "系统环境检查"

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "  ⚠️  winget 未安装，跳过包管理器安装"
    $HasWinget = $false
} else {
    Write-Host "  ✅ winget 可用"
    $HasWinget = $true
}

# ═══════════════════════════════════════════════
# Step 1: Install Hermes Agent
# ═══════════════════════════════════════════════
Write-Step "Step 1: 安装 Hermes Agent"

Invoke-Command 'winget install NousResearch.HermesAgent 2>$null'
if ($LASTEXITCODE -ne 0) {
    Write-Host "  winget 源未找到，尝试 pip 安装..."
    Invoke-Command 'pip install hermes-agent'
}

# ═══════════════════════════════════════════════
# Step 2: Verify Installation
# ═══════════════════════════════════════════════
Write-Step "Step 2: 验证安装"

$hermesCmd = Get-Command hermes -ErrorAction SilentlyContinue
if (-not $hermesCmd) {
    # 尝试查找 hermes.exe 路径
    $hermesExe = "$env:LOCALAPPDATA\hermes\.venv\Scripts\hermes.exe"
    if (Test-Path $hermesExe) {
        Write-Host "  ✅ Hermes found at: $hermesExe"
        $script:hermesExe = $hermesExe
    } else {
        Write-Warning "  ❌ Hermes not found in PATH. You may need to restart terminal."
        return
    }
} else {
    Write-Host "  ✅ Hermes found in PATH: $($hermesCmd.Source)"
    $script:hermesExe = "hermes"
}

# ═══════════════════════════════════════════════
# Step 3: Configure Hermes
# ═══════════════════════════════════════════════
Write-Step "Step 3: 写入配置"

# 创建 HermesHome 目录
if (-not (Test-Path $HermesHome)) {
    New-Item -ItemType Directory -Path $HermesHome -Force | Out-Null
}

# 复制 config.yaml
$configSrc = Join-Path $PackDir "config" "config.yaml"
$configDst = Join-Path $HermesHome "config.yaml"
if (Test-Path $configSrc) {
    Copy-Item -Path $configSrc -Destination $configDst -Force
    Write-Host "  ✅ config.yaml 已复制"
}

# 复制 SOUL.md
$soulSrc = Join-Path $PackDir "config" "SOUL.md"
$soulDst = Join-Path $HermesHome "SOUL.md"
if (Test-Path $soulSrc) {
    Copy-Item -Path $soulSrc -Destination $soulDst -Force
    Write-Host "  ✅ SOUL.md 已复制"
}

# 复制 .env 模板（仅当 .env 不存在时）
$envSrc = Join-Path $PackDir "config" ".env.template"
$envDst = Join-Path $HermesHome ".env"
if ((Test-Path $envSrc) -and -not (Test-Path $envDst)) {
    Copy-Item -Path $envSrc -Destination $envDst -Force
    Write-Host "  ✅ .env 模板已创建（请填入 API Key）"
}
elseif (Test-Path $envDst) {
    Write-Host "  ✅ .env 已存在，保留现有配置"
}

# ═══════════════════════════════════════════════
# Step 4: Install Skills
# ═══════════════════════════════════════════════
Write-Step "Step 4: 安装本地技能"

$skillsSrc = Join-Path $PackDir "skills"
$skillsDst = Join-Path $HermesHome "skills"

if (Test-Path $skillsSrc) {
    # 确保技能目录存在
    if (-not (Test-Path $skillsDst)) {
        New-Item -ItemType Directory -Path $skillsDst -Force | Out-Null
    }

    # 递归复制每个自定义技能
    Get-ChildItem -Path $skillsSrc -Recurse -Directory | ForEach-Object {
        $relPath = $_.FullName.Substring($skillsSrc.Length + 1)
        $targetDir = Join-Path $skillsDst $relPath
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
    }
    Get-ChildItem -Path $skillsSrc -Recurse -File | ForEach-Object {
        $relPath = $_.FullName.Substring($skillsSrc.Length + 1)
        $targetPath = Join-Path $skillsDst $relPath
        Copy-Item -Path $_.FullName -Destination $targetPath -Force
    }
    Write-Host "  ✅ 技能已安装到 $skillsDst"
}

# ═══════════════════════════════════════════════
# Step 5: Install ddgs dependency
# ═══════════════════════════════════════════════
Write-Step "Step 5: 安装额外 Python 依赖"

$hermesPip = Join-Path $HermesHome ".venv" "Scripts" "pip.exe"
if (Test-Path $hermesPip) {
    & $hermesPip install ddgs 2>&1 | Out-Null
    Write-Host "  ✅ ddgs 已安装（DuckDuckGo 搜索用）"
}

# ═══════════════════════════════════════════════
# Step 6: Enable toolsets
# ═══════════════════════════════════════════════
Write-Step "Step 6: 启用工具集 & 插件"

& $script:hermesExe tools enable x_search 2>&1 | Out-Null
& $script:hermesExe tools enable video 2>&1 | Out-Null
& $script:hermesExe tools enable spotify 2>&1 | Out-Null
& $script:hermesExe plugins enable disk-cleanup 2>&1 | Out-Null
& $script:hermesExe plugins enable google_meet 2>&1 | Out-Null
& $script:hermesExe plugins enable security-guidance 2>&1 | Out-Null
& $script:hermesExe plugins enable spotify 2>&1 | Out-Null
& $script:hermesExe plugins enable web/ddgs 2>&1 | Out-Null

Write-Host "  ✅ 工具集和插件已启用"

# ═══════════════════════════════════════════════
# 完成
# ═══════════════════════════════════════════════
Write-Step "✅ 部署完成" "🎉"
Write-Host ""
Write-Host "接下来你需要手动配置以下内容：" -ForegroundColor Yellow
Write-Host "  1️⃣  API Key: 在 $HermesHome\.env 中设置 DEEPSEEK_API_KEY" -ForegroundColor White
Write-Host "  2️⃣  模型配置: 运行 hermes model 选择模型/提供商" -ForegroundColor White
Write-Host "  3️⃣  (可选) Spotify: 运行 hermes auth spotify" -ForegroundColor White
Write-Host "  4️⃣  重启 Hermes 使插件生效" -ForegroundColor White
Write-Host ""
Write-Host "然后加载技能（新会话自动生效）：" -ForegroundColor Green
Write-Host "  hermes -s screenlingua" -ForegroundColor Green
Write-Host "  📖 详细说明见 README.md" -ForegroundColor Gray

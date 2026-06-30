#!/bin/bash
# Hermes Agent 一键部署脚本 (Linux/macOS)
# 用法: chmod +x setup.sh && ./setup.sh

set -euo pipefail

# Repo root is the directory containing this script.
# Keep this path calculation simple so a freshly cloned repo works on any machine.
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
PACK_DIR="$REPO_ROOT"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

echo "========================================"
echo " Hermes Agent 部署脚本 (Linux/macOS)"
echo "========================================"

# Step 1: Install Hermes Agent
echo ""
echo "⏳ Step 1: 安装 Hermes Agent"
if command -v hermes &> /dev/null; then
    echo "  ✅ Hermes 已安装"
else
    echo "  > 通过 curl 安装..."
    curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
    echo "  ✅ Hermes 安装完成"
fi

# Step 2: Write config
echo ""
echo "⏳ Step 2: 写入配置"
mkdir -p "$HERMES_HOME"

if [ -f "$PACK_DIR/config/config.yaml" ]; then
    cp "$PACK_DIR/config/config.yaml" "$HERMES_HOME/config.yaml"
    echo "  ✅ config.yaml 已复制"
fi

if [ -f "$PACK_DIR/config/SOUL.md" ]; then
    cp "$PACK_DIR/config/SOUL.md" "$HERMES_HOME/SOUL.md"
    echo "  ✅ SOUL.md 已复制"
fi

# Copy .env template (only if .env doesn't exist)
if [ -f "$PACK_DIR/config/.env.template" ] && [ ! -f "$HERMES_HOME/.env" ]; then
    cp "$PACK_DIR/config/.env.template" "$HERMES_HOME/.env"
    echo "  ✅ .env 模板已创建（请填入 API Key）"
elif [ -f "$HERMES_HOME/.env" ]; then
    echo "  ✅ .env 已存在，保留现有配置"
fi

# Step 3: Install skills
echo ""
echo "⏳ Step 3: 安装本地技能"
SKILLS_SRC="$PACK_DIR/skills"
SKILLS_DST="$HERMES_HOME/skills"
if [ -d "$SKILLS_SRC" ]; then
    mkdir -p "$SKILLS_DST"
    cp -r "$SKILLS_SRC/"* "$SKILLS_DST/"
    echo "  ✅ 技能已安装到 $SKILLS_DST"
fi

# Step 4: Install Python dependencies
echo ""
echo "⏳ Step 4: 安装 Python 依赖"
if command -v uv &> /dev/null; then
    uv pip install ddgs 2>/dev/null && echo "  ✅ ddgs 已安装" || echo "  ⚠️  ddgs 安装失败（可忽略）"
else
    pip install ddgs 2>/dev/null && echo "  ✅ ddgs 已安装" || echo "  ⚠️  ddgs 安装失败（可忽略）"
fi

# Step 5: Enable toolsets & plugins
echo ""
echo "⏳ Step 5: 启用工具集和插件"
hermes tools enable x_search 2>/dev/null || true
hermes tools enable video 2>/dev/null || true
hermes tools enable spotify 2>/dev/null || true
hermes plugins enable disk-cleanup 2>/dev/null || true
hermes plugins enable google_meet 2>/dev/null || true
hermes plugins enable security-guidance 2>/dev/null || true
hermes plugins enable spotify 2>/dev/null || true
hermes plugins enable web/ddgs 2>/dev/null || true
echo "  ✅ 工具集和插件已启用"

echo ""
echo "🎉 部署完成！"
echo ""
echo "接下来需要手动配置："
echo "  1️⃣  API Key: 在 $HERMES_HOME/.env 中设置 DEEPSEEK_API_KEY"
echo "  2️⃣  模型配置: hermes model"
echo "  3️⃣  (可选) Spotify: hermes auth spotify"
echo "  4️⃣  查看部署说明: cat $PACK_DIR/README.md"

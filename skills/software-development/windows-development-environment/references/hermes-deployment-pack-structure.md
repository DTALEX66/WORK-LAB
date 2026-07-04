# Hermes 跨机器部署包结构

## 仓库结构（当前）

```
hermes/                         # GitHub: DTALEX66/hermes
├── .gitattributes              # LF 换行规范
├── .gitignore                  # 排除 .env / auth.json
├── README.md                   # 部署说明（含三种路由方案 + CC Switch）
├── TROUBLESHOOTING.md          # 排坑手册
├── setup.ps1                   # Windows 部署脚本（不安装 Hermes 本体）
├── setup.sh                    # Linux/macOS 部署脚本
├── config/
│   ├── config.yaml             # 完整配置（GPT-5.5 + CC Switch 代理）
│   ├── SOUL.md                 # Agent 人格设定（中文）
│   └── .env.template           # 脱敏环境变量模板（含代理配置）
└── skills/
    ├── model-switch/SKILL.md   # 模型切换技能（DP/GPT）
    └── software-development/
        ├── screenlingua/       # 截图翻译项目
        ├── python-testing/     # Python 测试约定
        └── windows-development/# Windows 排坑
```

## 部署流程

### 新电脑（Windows）

```powershell
git clone git@github.com:DTALEX66/hermes.git
.\setup.ps1                     # 复制配置/技能/启用插件
```

### 部署后手动步骤

1. **设置 API Key** — 编辑 `%LOCALAPPDATA%\hermes\.env`
2. **OAuth 认证** — `hermes auth add openai-codex`（GPT 方案需要）
3. **启动 CC Switch**（如果网络受限需要翻墙）
4. **选择路由方案** — 按网络环境选方案，修改 config.yaml 或 `hermes config set`
5. `/reset` 或重启 Hermes

### setup.ps1 自动完成的内容

| 步骤 | 操作 |
|------|------|
| 1 | 复制 config.yaml / SOUL.md |
| 2 | 如 .env 不存在则从 .env.template 创建 |
| 3 | 安装本地技能到 skills/ 目录 |
| 4 | pip install ddgs |
| 5 | 启用工具集 x_search / video / spotify |
| 6 | 启用插件 disk-cleanup / google_meet / security-guidance / spotify / web/ddgs |

## 凭证注意事项

1. **永不提交** `.env` 或 `auth.json` 到 Git（有 `.gitignore` 保护）
2. **OAuth 令牌**（ChatGPT OAuth）存储在 `auth.json`，新电脑需重新运行 `hermes auth add openai-codex`
3. **CC Switch 安装包**不包含在仓库中（因体积大已被移除），需自行下载
4. **.env 中 `HTTPS_PROXY`** 写入后需**完全重启 Hermes** 才生效（环境变量在进程启动时读取）

## 路由方案速查

| 方案 | Provider | 环境要求 | 配置方式 |
|:----:|----------|---------|---------|
| DeepSeek 直连 | `deepseek` | `api.deepseek.com` 可达 | `.env` 设 `DEEPSEEK_API_KEY` |
| GPT OAuth | `openai-codex` | `chatgpt.com` 可达 | `hermes auth add openai-codex` |
| GPT + 代理 | `openai-codex` + `HTTPS_PROXY` | CC Switch 运行中 | 同上 + `.env` 设代理 |

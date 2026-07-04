# Hermes 凭证审计与模板化

## 审计步骤

部署包上传前，检查现有凭证是否含有过时/无用项目密钥：

### 1. 读取 .env 中的有效密钥

```bash
cat "$HERMES_HOME/.env" | grep -v '^#' | grep -v '^$'
```

输出示例：
```
DEEPSEEK_API_KEY=sk-a02...66b3
```

如果只有 1 个密钥且是当前正在用的提供商，无需清理。

### 2. 读取 auth.json 中的凭证池

```bash
cat "$HERMES_HOME/auth.json" | python3 -c "
import sys,json
d=json.load(sys.stdin)
pools = d.get('credential_pool', {})
print(f'提供商数: {len(pools)}')
for name, creds in pools.items():
    print(f'  {name}: {len(creds)} 个凭证')
    for c in creds:
        print(f'    - source: {c.get(\"source\",\"?\")}, base_url: {c.get(\"base_url\",\"?\")}')
"
```

### 3. 创建脱敏模板

- `.env.template`: 复制 .env → 将实际密钥值替换为 `你的XXX密钥` 占位符
- `auth.json.template`: 复制 auth.json → 清空 `secret_fingerprint` → 将 `id` 改为 `new`

### 4. 添加 .gitignore

```gitignore
# 凭证文件
.env
auth.json

# 操作系统
.DS_Store
Thumbs.db

# Python
__pycache__/
*.pyc
.venv/
```

## 典型单提供商场景

多数用户只有 1 个活跃的 AI 提供商，.env 中只有 1 个未注释的密钥行。此时：
- 不需要逐行清理（因为没有多余的）
- 但必须创建 `.env.template` 让新机器知道要填什么
- auth.json 也只需一个 deepseek 凭证池条目作为模板

## 部署脚本集成

setup.ps1 / setup.sh 应包含：

```powershell
# 如果 .env 不存在，从模板创建
if (Test-Path ".env.template") -and -not (Test-Path "$HermesHome\.env") {
    Copy-Item ".env.template" "$HermesHome\.env"
    Write-Host "✅ .env 模板已创建（请填入 API Key）"
}
```

这样新机器克隆后一键部署，自动获得需要填写的 .env 文件。

# 部署排坑手册

> 记录 DTALEX66/hermes 部署过程中遇到的错误及解决方法

---

## 1. Git Clone HTTPS 被重置

**现象：**
```
fatal: unable to access 'https://github.com/DTALEX66/hermes.git/': Recv failure: Connection was reset
```

**原因：** 网络环境（被墙/代理）导致 HTTPS 连接被重置。

**解决：** 改用 SSH 克隆
```bash
git clone git@github.com:DTALEX66/hermes.git
```
前提：已配置 GitHub SSH 密钥（`~/.ssh/id_ed25519_github`）。

---

## 2. setup.ps1 编码错误

**现象：**
```
powershell.exe -File setup.ps1
# 大量乱码 + ParserError: MissingEndParenthesisInFunctionParameterList
```

**原因：** PowerShell 脚本含中文注释，从 bash (MSYS) 调用时编码不兼容。

**解决：** 不走 PowerShell，用 bash 手动执行各步骤：
- `cp` 复制配置文件
- `cp -r` 复制技能
- `pip install ddgs`
- `hermes tools enable` / `hermes plugins enable`

---

## 3. setup.ps1 路径错误

**现象：** 脚本设置 `$PackDir = Join-Path $RepoRoot "hermes-pack"`，但仓库根目录就是打包内容，没有 `hermes-pack/` 子目录。

**解决：** 修改为 `$PackDir = $RepoRoot`
```powershell
# 改前
$PackDir = Join-Path $RepoRoot "hermes-pack"
# 改后
$PackDir = $RepoRoot
```

---

## 4. .env 缺少代理配置

**现象：** 部署保留了现有 `.env`，但 CC Switch 代理变量未写入。

**解决：** 手动追加
```bash
cat >> ~/AppData/Local/hermes/.env << 'EOF'
HTTPS_PROXY=http://127.0.0.1:7890
HTTP_PROXY=http://127.0.0.1:7890
EOF
```

---

## 5. OAuth 认证超时

**现象：**
```
hermes auth add openai-codex
# [Command timed out after 30s]
```

**原因：** OAuth 设备码流程需要用户在浏览器中完成授权，前台 30s 超时不够。

**解决：** 后台运行 + 加长超时 + 设置代理
```bash
export HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890
hermes auth add openai-codex &  # 或 background=true
```
然后在浏览器打开 `https://auth.openai.com/codex/device` 输入验证码。

---

## 6. OAuth 页面被 Cloudflare 拦截

**现象：** 浏览器打开 `auth.openai.com/codex/device` 显示"正在进行安全验证"（Cloudflare 质询）。

**原因：** 沙箱浏览器 / 非代理浏览器无法通过 Cloudflare 验证。

**解决：** 在用户自己的浏览器中完成，确保浏览器走 CC Switch 代理（127.0.0.1:7890）。

---

## 7. python3 命令不可用

**现象：**
```
Python was not found; run without arguments to install from the Microsoft Store
```

**原因：** Windows 上 `python3` 被 Microsoft Store 占位，实际 Python 是 `python`。

**解决：** 使用 `python` 而非 `python3`。

---

## 8. Git 提交缺少身份信息

**现象：**
```
Author identity unknown
fatal: unable to auto-detect email address
```

**解决：** 临时指定或全局设置
```bash
# 临时（单次提交）
git -c user.name="DTALEX66" -c user.email="your@email.com" commit -m "..."

# 永久
git config --global user.name "DTALEX66"
git config --global user.email "your@email.com"
```

---

## 9. 模型切换必须 /reset

**现象：** 改了 `hermes config set model.provider` 后模型没变。

**原因：** Hermes 在会话启动时锁定 Provider，中途改配置不影响当前会话。

**解决：** 改完配置后执行 `/reset` 或重启 Hermes。

---

## 快速参考

| 想做什么 | 命令 |
|----------|------|
| 切到 DeepSeek | `hermes config set model.provider deepseek` + `/reset` |
| 切到 GPT | `hermes config set model.provider openai-codex` + `/reset` |
| 检查连通性 | `curl -x http://127.0.0.1:7890 -sI https://chatgpt.com` |
| 环境健康 | `hermes doctor` |
| 查看 OAuth | `hermes auth list` |

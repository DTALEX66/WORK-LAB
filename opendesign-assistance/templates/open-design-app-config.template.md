# Open Design Config Template

这个模板说明本仓库期望写入 Open Design `app-config.json` 的关键字段。

实际配置不要直接复制本文件；推荐运行：

```bash
python opendesign-assistance/scripts/configure_open_design_windows.py \
  --project-root "D:\All projects\OPEN-DESIGN-Assistance"
```

## 关键字段

```json
{
  "agentId": "codex",
  "agentModels": {
    "codex": {
      "model": "gpt-5.5"
    }
  },
  "agentCliEnv": {
    "codex": {
      "CODEX_BIN": "C:\\Users\\<user>\\AppData\\Local\\OpenAI\\Codex\\bin\\<version>\\codex.exe",
      "CODEX_HOME": "C:\\Users\\<user>\\.codex"
    }
  },
  "projectLocations": [
    {
      "id": "loc_open_design_assistance",
      "name": "OPEN-DESIGN-Assistance",
      "path": "D:\\All projects\\OPEN-DESIGN-Assistance"
    }
  ],
  "defaultProjectLocationId": "loc_open_design_assistance"
}
```

## 安全边界

不要把以下内容放入仓库：

```text
.codex/auth.json
OpenAI API Key
OAuth access token
Refresh token
.env
真实 AppID / adUnitId
```

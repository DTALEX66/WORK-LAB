# Hermes Token Monitor

`scripts/workflow/token_monitor.py` 是一个本地 Windows/Tkinter 桌面监视器，用来跟踪 Hermes 或其它 OpenAI-compatible 客户端产生的 JSON/JSONL usage 日志。

## 设计边界

- 只统计日志中明确出现的 `prompt_tokens`、`input_tokens`、`completion_tokens`、`output_tokens`、`total_tokens`；
- 不根据字符数、字节数或文本长度估算 token；
- `total_tokens` 缺失时，仅在 input 和 output 都是明确整数时计算二者之和；
- 没有 usage 的行只计入“未识别行”，不计入 token；
- 不显示原始 prompt、response、日志行、API key、OAuth、Cookie 或认证内容；
- 文件以只读方式增量跟踪，支持追加、truncate 和日志轮转；
- 默认不会打开或读取日志，必须在窗口点击“开始监控”。

## 启动

从仓库根目录运行：

```powershell
python scripts/workflow/token_monitor.py
```

指定日志：

```powershell
python scripts/workflow/token_monitor.py `
  --file "$env:LOCALAPPDATA\hermes\logs\agent.log"
```

默认路径为：

```text
%LOCALAPPDATA%\hermes\logs\agent.log
```

窗口显示：

- 输入 token；
- 输出 token；
- 总 token；
- 已识别请求数；
- 未识别日志行数；
- 按模型聚合统计。

## 自检与测试

不打开 GUI 的自检：

```powershell
python scripts/workflow/token_monitor.py --self-test
```

预期：

```text
TOKEN_MONITOR_SELF_TEST_PASS
```

项目测试：

```powershell
python -m unittest tests.test_token_monitor -v
```

## 重要限制

### API 路由

如果 Kimi、DeepSeek 或 OpenAI API 返回标准 usage 字段，监视器可以记录实际 usage。

### Codex OAuth

`openai-codex` OAuth 链路不保证把完整 usage 字段写入 Hermes 日志。如果日志没有真实 usage，窗口会显示未识别行，不会制造一个看似精确的估算数字。

因此本软件区分：

```text
真实 usage：计入
缺少 usage：不计入，只提示未识别
字符估算：不支持
```

### 隐私

监视器不会上传日志，也不会写入 Hermes Home。日志路径由用户在本机选择；请不要把包含真实凭据或敏感 prompt 的日志复制到仓库。运行时临时文件遵循项目 `.hermes/task-runtime/` 边界。

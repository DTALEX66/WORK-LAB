# Wrapper run 三坑：复现、诊断与端到端验证（validated 2026-08-14）

场景：Windows + Git-Bash，所有 terminal 命令经 `python "<HERMES_HOME>/bin/hermes-project-data.py" --project . run -- <child>`。

## 1. PYTHONPATH 注入遮蔽项目 venv

复现：

```bash
# 项目 venv 的 python 却从 Hermes venv 导包
.venv/Scripts/python -c "import os, sys; print(os.environ.get('PYTHONPATH')); print([p for p in sys.path if 'site-packages' in p])"
# PYTHONPATH= C:\Users\ALEX\AppData\Local\hermes\hermes-agent;C:\Users\ALEX\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages
# SITEP= ['C:\...\hermes-agent\venv\Lib\site-packages', 'D:\...\.venv\Lib\site-packages']   <- Hermes 排最前

# 症状：同一 venv 一个包能导、一个包炸
.venv/Scripts/python -c "import yaml; print(yaml.__version__)"            # OK 6.0.3（恰好兼容）
.venv/Scripts/python -c "import jsonschema; print(jsonschema.__version__)" # ModuleNotFoundError: No module named 'rpds.rpds'
```

修复：

```bash
python "<HERMES_HOME>/bin/hermes-project-data.py" --project . run -- env -u PYTHONPATH .venv/Scripts/python scripts/xxx.py
```

用真实 jsonschema 校验 YAML/JSON schema 的验证脚本模式：`env -u PYTHONPATH .venv/Scripts/python .hermes/task-runtime/validate.py`，首轮校验抓到 3 个真实 schema 违规 → 修正 → 复跑 PASS（证明校验链真实生效）。

## 2. 子进程 GBK 输出打爆 wrapper UTF-8 管道

复现：`powershell -NoProfile -ExecutionPolicy Bypass -File test.ps1`（PS 5.1，脚本里有中文 Write-Host）：

```
Exception in thread Thread-5 (_readerthread): ... UnicodeDecodeError: 'utf-8' codec can't decode byte 0xcd in position 387
```

exit_code=0 但输出全丢（reader 线程静默失败）。

修复（被调 .ps1 开头）：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

中文结果落盘再读：`$result | Out-File -FilePath ".hermes\task-runtime\results.txt" -Encoding utf8`，然后 read_file。

## 3. guard 拦截内联 `$`

`powershell -NoProfile -Command "$PSVersionTable.PSVersion.ToString()"` → `PROJECT DATA BOUNDARY BLOCKED: shell expansion before wrapper execution is forbidden`。

修复：写 .ps1 到 `.hermes/task-runtime/` 再执行：

```powershell
# check_ps1.ps1 —— PS1 语法检查模式
$files = @("scripts/Enter-ArcheAxisDev.ps1", "scripts/Exit-ArcheAxisDev.ps1")
foreach ($f in $files) {
    try { [void][scriptblock]::Create((Get-Content -Raw -Path $f)); Write-Output ("SYNTAX_OK=" + $f) }
    catch { Write-Output ("SYNTAX_FAIL=" + $f) }
}
```

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File .hermes/task-runtime/check_ps1.ps1
```

## 4. 交付 PS1 的中文编码：UTF-8 with BOM

write_file 写出 UTF-8 无 BOM；PS 5.1（5.1.26100）解析中文注释乱码。交付后重编码：

```python
raw = open(path, "rb").read()
text = raw.decode("utf-8")
open(path, "wb").write(b"\xef\xbb\xbf" + text.encode("utf-8"))
```

## 5. 会话环境脚本端到端验证模式（Enter/Exit 类脚本）

在**隔离 powershell 进程**里跑完整生命周期（进程退出即无副作用），结果落盘断言：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$result = @()
& .\scripts\Enter-X.ps1 | Out-Null
$result += ("CHECK_VAR=" + $env:SOME_VAR)          # 期望真实路径
& .\scripts\Exit-X.ps1 | Out-Null
$result += ("AFTER_EXIT_VAR_EMPTY=" + [bool]$env:SOME_VAR)   # 期望 False = 已清除
$result | Out-File ".hermes\task-runtime\results.txt" -Encoding utf8
```

注意 `[bool]$env:VAR` 的语义：变量被移除后为空串 → False；False 即"已清理"。

## 6. 附带：read_file 把合法 UTF-8 判成 binary

`read_file` 对部分合法 UTF-8 .md（含 em-dash 等）报 "Binary file"，但 `file` 命令与 python 解码均正常（无 NUL）。读法：小脚本 `open(path,'rb').read()` 按 utf-8/utf-16/gb18030 逐个尝试解码并打印；不要凭 read_file 的 binary 提示断定编码。

## 7. 工具探测模式（inventory 扫描器）

工具链探测"仓内优先、PATH 回退"：先查仓库内已知路径（scoop shims、rustup toolchains/*/bin），再 `shutil.which`；子进程用 `creationflags=CREATE_NO_WINDOW`；多行输出（`tesseract --list-langs`）单独用完整捕获函数，别用"取第一行"的版本探测函数。machine_id 用 `sha256(hostname)[:12]`，不写主机名明文。

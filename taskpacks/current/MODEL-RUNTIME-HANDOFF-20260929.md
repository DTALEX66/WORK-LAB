# WORK-LAB 本机模型服务 · 交接记录（2026-09-29）

**性质**：交接记录（handoff record），**不是**新的任务权威、**不是**执行授权。
`currentTaskpack`（`WORK-LAB-UNIFIED-PRODUCT-CONVERGENCE-TASKPACK-20260918`）仍权威。
**取代**：`MODEL-GOVERNANCE-HANDOFF-20260928.md` 的运行时分配表（该表记 FAST 在 llama.cpp :8081、
EMBEDDING/OCR 在 Ollama，均已失效）。09-28 记录作为历史保留不改写。

---

## 0. 摘要（本会话一米以内说完）

用户指令序列：①删除 Ollama，用 LM Studio 接收/部署/迁移/配置；②下载走国内通道，不占个人 VPN；
③确保 LM Studio 与模型任务全部完成（含配置调教部署），因为**用户不会使用 LM Studio**。

结果：Ollama **已卸载**（零权重误删）；6 条能力线全部落在 **LM Studio :1234 单一运行时**；
服务做成**无人值守**（开机自启 + 登录预热 + 每 10 分钟自愈）；参数经实测调教；
**最终验收 8/8 PASS**；服务端与本地仓库**完全一致**。

---

## 1. 结论

```
ARCHEAXIS_LOCAL_AI_BASE  = PARTIAL   # 6 条能力线均可用；ArcheAxis 侧真实适配器未接入
SHARED_MODEL_RUNTIME     = PASS      # 单一运行时，单份权重，6 条线卸载后复验全过
WORKLAB_MODEL_GOVERNANCE = PASS      # 登记表与实测一致；重排保真度记 PARTIAL（已显式标注）
WORKLAB_COMMAND_CENTER   = BLOCKED   # 本会话未动，无实现
WORKLAB_ROUTER_E2E       = BLOCKED   # 本会话未动，无实现
WORKLAB_UI_ACCEPTANCE    = BLOCKED   # 本会话未动，无实现
```

`PASS` 的依据是**可复现证据**，不是"文件存在/接口 200/模型已下载"。

## 2. 最终结构（单一运行时）

| 档位 | 模型 | 体积 | 调用模型名 | 常驻策略 | 授权 |
|---|---|---|---|---|---|
| FAST | Qwen3.5-4B Q4_K_M | 2.74 GB | `qwen3.5-4b` | **常驻**（ttl 24h） | 三项目共享 |
| DEEP | Qwen3.8-27B UD-IQ4_XS | 14.25 GB | `qwen3.8-27b` | 按需（冷启 17–29s） | 三项目共享 |
| EMBEDDING | Qwen3-Embedding-0.6B Q8_0 | 0.64 GB | `text-embedding-qwen3-embedding-0.6b` | 按需（3.3s） | ArcheAxis 优先 |
| RERANK | Qwen3-Reranker-0.6B Q8_0 | 0.49 GB | `qwen3-reranker-0.6b` | 按需（3.2s） | ArcheAxis 优先 |
| OCR | Qwen2.5-VL-7B-Instruct + mmproj | 5.54 GB | `qwen2.5-vl-7b-instruct` | 按需（5.4s） | ArcheAxis 优先 |
| ASR | faster-whisper-large-v3-turbo | 1.51 GB | 进程内 | — | ArcheAxis 优先 |

端点统一：`http://127.0.0.1:1234/v1`（OpenAI 兼容，仅回环，无需 Key）。

**保留未删（待用户决定）**：`qwen3:8b`（5.22 GB）、`qwen3-coder-30b-a3b`（18.56 GB）。
**删除权重数 = 0。**

## 3. 关键实测数据

| 项 | 值 |
|---|---|
| FAST 吞吐 | **77.9 tok/s**（reasoning tokens 0）；warm 峰值 90.41 |
| DEEP 冷启 / 吞吐 | 21.9–28.6 s / **1.977 tok/s**（自动显存分配） |
| EMBEDDING | **1024 维**；中英同义 0.8340 vs 异义 0.3396，分离度 **+0.4944** |
| RERANK | 二值判定，含高难干扰项全对；**无分数**（见 §6） |
| OCR | **8/8 行逐字精确，两轮一致**，5.3–13.8 s |
| 显存（FAST 常驻） | 1450–3751 MiB used / 6446–4145 MiB free（其余应用波动） |
| 三模型同时驻留 | 7673 / 8151 MiB → **会挤爆，故不采用** |

## 4. 调教结论（含两次假设被数据推翻）

| 决策 | 结果 | 依据 |
|---|---|---|
| FAST `parallel` | **1**（默认 4） | 实测省 **153 MiB** 且略快（77.28 vs 75.91 tok/s） |
| DEEP GPU offload | **保持自动** | 自动 1.977 ＞ gpu=max 0.817 ＞ gpu=0.6 0.911 ＞ gpu=0.75 0.781 ＞ gpu=0.9 0.825 |
| DEEP 是否常驻 | 否 | 与 FAST+VLM 同驻会占满显存 |
| 参考路径 | llama.cpp `-ngl 32` 达 2.52 tok/s（快约 27%） | 保留为可选逃生通道，不自动启动 |

## 5. 无人值守机制（用户不操作 GUI）

| 事项 | 机制 | 验证方式 |
|---|---|---|
| 服务随 LM Studio 自启 | `autoStartOnLaunch` 由 **false 改 true** | 杀掉 GUI → 重启 → 服务无人工干预恢复 |
| 登录预热 | 计划任务 `WORK-LAB LM Studio warm-up`（登录+90s） | `LastTaskResult = 0`；卸载后自动重载 FAST |
| 崩溃自愈 | 计划任务 `WORK-LAB LM Studio health`（每 10 分钟） | **真杀掉 LM Studio** → 端点恢复 HTTP 200 并重载 FAST；健康时静默（日志增 0 字节） |
| 重复实例清理 | 脚本数**精确标识符**，清理 `name:2` | 故意造重复 → 脚本检测并卸载 |

脚本位置：`%LOCALAPPDATA%\WORK-LAB\lmstudio-autostart.ps1`、`lmstudio-heal.ps1`、
`register-autostart-task.ps1`（可重复执行）。
用户说明：`%LOCALAPPDATA%\WORK-LAB\README-本地模型服务.md`。

## 6. 三个必须知道的限制（真实边界，非故障）

1. **重排只有二值判定**。LM Studio 0.4.25 **无 `/v1/rerank`**（三处端点全拒），且
   **从不返回 logprobs**（连普通已加载 LLM 都是 `null`）。判断准确但**两个合格候选无法排序**。
   旧记录的 `score_spread 0.9996` 来自 llama.cpp，已标记 **NOT REPRODUCIBLE ON LM STUDIO**。
2. **`qwen3.5-4b` 必须带 `reasoning_effort:"none"`**，否则思考过程吃光输出预算、**正文为空**。
   `chat_template_kwargs{enable_thinking:false}` 与 `/no_think` **实测均无效**。
   此怪癖**只影响 4B**，27B 三通道正常。
3. **OCR 曾无法靠迁移解决**。Ollama 的 `qwen2.5vl:7b` blob 经 GGUF 头解析
   `hasVision=false`（无 `clip.*` 键）、manifest 仅一层、全库无 mmproj，**任何运行时都无法做视觉**。
   已改绑 `ggml-org/Qwen2.5-VL-7B-Instruct-GGUF`（模型 + 配对 mmproj，LM Studio 自动配对为 `type=vlm`）。

## 7. 遗留

| 项 | 状态 |
|---|---|
| ArcheAxis 侧真实适配器接入 | **未做** — 6 条能力线可用，但未接任何真实消费者 |
| Command Center / LAB Router / UI 验收 | **未做** — 三项均无实现（BLOCKED） |
| Rerank 分数 | **不可得**（LM Studio 限制）；若必须要分数，唯一已验证路径是 llama.cpp `/v1/rerank` |
| OCR 完整测试矩阵 | **未跑** — 仅中英混排单页 8/8；zh/en/mixed/PDF/scanned/table/page-order 未覆盖 |
| ASR 本轮复测 | **未做** — 只核验运行时与权重存在；此前实测结果仍有效但非本轮新证据 |
| `qwen3:8b`、`qwen3-coder-30b-a3b` | **保留未删**，超出"恰好 2 个通用 LLM"目标，待用户决定 |
| Ollama 制品库残留 27.71 GB | **保留未删**（16 blobs / 5 manifests），待用户决定 |
| `docs/future/WORK-LAB-SUPER-ENTRY-...md` | **故意不跟踪** — 其 JWT/OAuth2/Vault 章节与"无鉴权"铁律冲突 |

## 8. 阻塞

| 阻塞 | 性质 | 解锁条件 |
|---|---|---|
| 8 GiB 显存 | 物理约束 | 无法解决；DEEP 只能部分 offload（1.977 tok/s 已是本机最优自动值） |
| LM Studio 无重排端点 / 无 logprobs | 运行时能力边界 | 上游支持，或改由 llama.cpp 提供该能力 |
| `qwen3.5-4b` 参数怪癖 | 运行时行为 | 调用方统一带 `reasoning_effort:"none"`（已写入登记表与用户文档） |
| 分支退役 | **治理需授权** | `BRANCH-RETIREMENT-LEDGER` 标注 `PENDING_USER_AUTHORIZATION`；本会话未删除任何分支，只做了本地陈旧引用 prune 与已合并本地分支清理 |

## 9. 仓库一致性（本会话末次核验）

```
服务端 refs/heads          = main 仅此一个
服务端 main                = af4824bc5fa12977b0b7976145cb7456ec87dec3
本地 origin/main           = af4824bc5fa12977b0b7976145cb7456ec87dec3
本地 HEAD                  = af4824bc5fa12977b0b7976145cb7456ec87dec3
本地分支                   = main 仅此一个
领先/落后                  = 0 / 0
```

**澄清一处我先前的错误**：我曾把 `git branch -r` 显示的 18 条读成"18 个远程分支"。
实际那是**陈旧本地远程跟踪引用**；执行 `git fetch origin --prune` 后只剩 `origin/HEAD` 与
`origin/main`，`git ls-remote --heads origin` 证实**服务端只有 main**。本次已清理 8 个已核验的
本地分支（4 个本会话已合并 + 3 个有 MERGED PR + 1 个独有提交为 0）。

## 10. 下载通道策略（用户要求，已强制）

`huggingface.co` 在本机解析到 **157.240.10.36（Facebook 地址，DNS 污染）**，且系统代理
`127.0.0.1:7890` 已启用 → 任何 HF 请求都会消耗用户 VPN。

- 首选：`modelscope`（26–29 MiB/s）、`hf-mirror`（8 连接达 13.4 MiB/s）、`gh-proxy`
- **默认禁止**：`huggingface.co`、`cdn-lfs*.huggingface.co`（需显式 `--allow-remote`）
- 统一下载器 `wl_model_download.py` **在建立连接前就拒绝境外地址**（已测试：返回 `ROUTE_REFUSED`）
- **不使用 `lms get`**：它走 huggingface.co 且模型搜索是交互式的，无法脚本化与审计

## 11. 复核入口

```
迁移报告      reports/MODEL-RUNTIME-MIGRATION-OLLAMA-TO-LMSTUDIO-20260929.md
下载策略      .project/governance/model-download-policy.json
运行时登记表  .project/governance/runtime-registry.json
能力登记表    .project/governance/provider-registry.json
模型登记表    .project/governance/model-registry.json
最终验收      .project-local/runs/model-governance-20260928/final-acceptance.json
卸载前基线    .project-local/runs/model-governance-20260928/ollama-protection-baseline.json
证据归档      .project-local/artifacts/model-runtime-migration-20260929/  (63 文件, MANIFEST sha256)
用户说明      %LOCALAPPDATA%\WORK-LAB\README-本地模型服务.md
```

## 12. 本次相关 PR（全部 squash 合并，CI 24/24 绿）

| PR | 内容 |
|---|---|
| #154 | 模型 Provider 从 Ollama 迁移到 LM Studio（含 2 处我自己早前判断的更正） |
| #155 | 国内通道路由策略 + 权重来源更正 |
| #156 | 无人值守部署记录（自启、自愈、调优） |
| #157 | FAST parallel 调优 + 重复实例缺陷修复 |

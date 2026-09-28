# WORK-LAB 本机模型治理 · 交接记录（2026-09-28）

**性质**：交接记录（handoff record），**不是**新的任务权威、**不是**执行授权。
`currentTaskpack`（`WORK-LAB-UNIFIED-PRODUCT-CONVERGENCE-TASKPACK-20260918`）仍权威。
登记位置：`.project/governance/` 的模型治理机器真相 + 本记录。

**目标（用户 2026-09-28 指令）**：由 WORK-LAB 统一完成本机模型资源的部署、运行时配置、
能力注册、健康检查、性能验证与共享治理；ArcheAxis 得到完整但精简的本地 AI 底座；
WORK-LAB 得到统一模型运行与治理能力；DESIGN-LAB 与 WORK-LAB 共享必要公共能力；
**整个本机只维护一份模型资产**。

---

## 1. 结论

```
ARCHEAXIS_LOCAL_AI_BASE  = PARTIAL   # 14 项需求：9 PASS / 5 PARTIAL / 0 BLOCKED
SHARED_MODEL_RUNTIME     = PASS
WORKLAB_MODEL_GOVERNANCE = PASS
```

## 2. 最终结构（brief §九/§十八，未膨胀）

| 档位 | 模型 | 体积 | Runtime | 端点 | 授权 |
|---|---|---|---|---|---|
| FAST | Qwen3.5-4B Q4_K_M | 2.55 GB | llama.cpp | :8081 | 三项目共享 |
| DEEP | Qwen3.8-27B UD-IQ4_XS | 13.27 GB | llama.cpp | :8080 | 三项目共享 |
| EMBEDDING | Qwen3-Embedding-0.6B（复用） | 0.60 GB | Ollama | :11434 | ArcheAxis 优先 |
| RERANK | Qwen3-Reranker-0.6B（复用） | 0.46 GB | llama.cpp | :8082 | ArcheAxis 优先 |
| OCR | qwen2.5vl:7b（复用） | 5.56 GB | Ollama | :11434 | ArcheAxis 优先 |
| ASR | faster-whisper-large-v3-turbo（复用） | 1.51 GB | 进程内 | — | ArcheAxis 优先 |

另有 4 个 standby **保留未删**：`qwen3:8b`、`qwen3-coder:30b-a3b-q4_K_M`、sherpa-onnx SenseVoice、
sherpa-onnx streaming-zipformer-zh-14M。**删除数 = 0。**

## 3. 下载登记（Inventory → Hash → Identify → Reuse → Missing → Download，国内源优先）

| 模型 | 字节 | 来源 | 速率 | sha256 | license |
|---|---|---|---|---|---|
| Qwen3.5-4B Q4_K_M | 2,740,937,888 | ModelScope `unsloth/Qwen3.5-4B-GGUF` | 28–29 MB/s | `00fe7986…ef11a4` | apache-2.0 |
| Qwen3.8-27B UD-IQ4_XS | 14,252,845,984 | ModelScope `unsloth/Qwen3.8-27B-GGUF` | 26.6 MB/s | `40fac405…0e6199` | apache-2.0 |
| llama.cpp b11221 win-cuda-12.4 | 264,519,230 | GitHub release via gh-proxy.com | 1.7–3.0 MB/s | `95e15aa4…a267d1` | MIT |

本机实测：huggingface.co 与 hf-mirror.com **不可达**；GitHub 直连 **77 KB/s**；Ollama CDN **136 KB/s**。

**跳过（不再下载）**：Qwen3.5-9B/27B/35B-A3B/122B · 第二套 Embedding · 第二套 Reranker ·
PaddleOCR-VL / PP-OCRv6 · Qwen3-ASR-0.6B · Ollama 0.34.4 升级。

## 4. 实测关键数据

| 项 | 值 |
|---|---|
| DEEP（ngl=32, t=14） | prompt **20.10** / gen **2.52** tok/s |
| DEEP（ngl=0，GPU 被占时） | prompt 14.54 / gen 1.32 tok/s |
| FAST（ngl=99, t=14） | prompt **114.20** / gen **10.81** tok/s |
| 对照 MoE `qwen3-coder:30b-a3b` | gen 7.81 tok/s |
| DEEP 冷启 / 重启恢复 | 21.6s / 9.5s |
| DEEP 并发 2 | 各 27.38s / 1.415 tok/s（排队，非吞吐） |
| DEEP 超长上下文 | 40052 tok @c=8192 → HTTP 400 `exceed_context_size_error`（fail-closed） |
| Reranker | spread **0.9996**，1.77s / 5 候选 |
| OCR | 中英混排页：英文全中 + 中文 **6/6**，61.7s |
| ASR | 4.49s 中文音频 → **逐字正确**，RTF 1.5 |
| E2E | **11/11 PASS**（真实模型 + 真实夹具，无 mock） |
| 磁盘 | 共享库 81.66 → **97.49 GB**（净增权重 +15.82 GB）；回收 partial **3.16 GB** |

## 5. 遇到的问题与处置（完整）

见 `.project-local/runs/model-governance-20260928/HANDOFF.md` §4 的 P1–P10。要点：
brief 型号本机不存在（先核验再下载）· HF 全不可达（改 ModelScope）· Ollama CDN 136 KB/s 导致
4B 改由 llama.cpp 直接读共享库单份文件 · 27B 受桌面占用 GPU 限制（用户释放后 +91%）·
Qwen3.5/3.8 是推理模型必须关思考 · 我一度误判 reranker 无区分度并已按实测更正 ·
Ollama 无 rerank 接口（交 llama.cpp）· **删除前核验拦下 0.46 GB 的错误删除**（两文件同为
494,879,360 B 但 sha256 不同）。

## 6. 阻塞

**无硬阻塞。** 未闭环项：
1. `runtimes-tmp/reranker-dl.gguf`（0.46 GB）—— 与在用 reranker **不是重复**（哈希不同），
   待用户决定"纳入备用"或"确认后删除"。
2. ArcheAxis 侧 5 项 PARTIAL（候选落库 / 人类学习工作流 / machine-competence 契约 /
   长文档全量批跑 / 带真实 CJK 字体的 PDF 解析）—— 属 ArcheAxis 工程，**非模型能力缺失**。
3. 27B 的交互速度受硬件限制（内存带宽天花板 ≈2.7 tok/s，实测 2.52 = 93%）；
   提速只有"更小量化"或"更大 GPU"，**不得**再下载多个 20–30B 替代模型。

## 6.5 证据归档（本地，可校验）

原始证据已按仓库既有归档惯例整理到 `.project-local/artifacts/model-governance-20260928/`：

| 目录 | 内容 |
|---|---|
| `01-docs/` | CLOSEOUT、本 HANDOFF、下载前登记、commit message、PR 正文、项目 PR 全表 |
| `02-machine-snapshot/` | 变更前只读机器盘点（逐文件 sha256） |
| `03-benchmark/` | DEEP/FAST 吞吐、offload 阶梯、线程与上下文敏感性 |
| `04-e2e/` | 真实全链路 E2E（11/11）、DEEP 生命周期/并发/重启/超长上下文 |
| `05-lmstudio/` | LM Studio 接入实测：索引、端口、加载生命周期、吞吐、参数差异 |
| `06-download/` | 可续传+哈希校验下载器、盘点器、保护快照器、清单生成器 |
| `07-protection/` | 变更前保护快照与回滚方案 |
| `fixtures/` | E2E 真实输入（中英 md/txt、生成 PDF、CJK PNG、中文 WAV） |

- 清单（**逐文件 sha256**）：`MANIFEST.json` · 说明：`ARCHIVE-README.md` · 规模 59 文件 / 546 KB
- 排除：一次性 8 MiB 范围探测（可由 `ms_download.py` 复现）、浏览器 profile 临时目录
- 校验：按 `MANIFEST.json` 的 sha256 逐文件比对即可证明归档未被篡改
## 7. 证据与交付物

- 机器真相：`.project/governance/` 7 份 JSON（model / runtime / provider / capability /
  permission / archeaxis-pipeline / benchmark）。
- 交付报告：`reports/MODEL-GOVERNANCE-20260928.md`。
- Closeout（20 项交付逐条）：`.project-local/runs/model-governance-20260928/CLOSEOUT.md`。
- 交接文档：同目录 `HANDOFF.md`；下载前登记：`DOWNLOAD-PLAN-20260928.md`。
- 原始证据：同目录 `protection-baseline.json` `inventory.utf8.json` `bench-deep*.json`
  `deep-serving.json` `deep-usability.json` `e2e-results.json` `e2e-console.log` + 全部脚本。
- Git：PR #146 → `main d4f9723`；PR #147 → GPU 释放后重测更新。

## 8. 边界（本轮明确未做）

未删除任何现有模型/文件（3.16 GB partial 除外，且删除前已核验并确认非模型）；
未升级 Ollama（0.34.4 包保持未安装）；未改全局产品配置；未读取任何凭据；
**权重零入 Git**；未为"以后可能有用"下载任何模型。

## 9. 后续任务（未授权执行，需先解决冲突）

`docs/future/WORK-LAB-SUPER-ENTRY-COMMAND-CENTER-LAB-ROUTER-2026-09-27.md`
（用户 2026-09-28 再次确认）：超级入口 / Command Center / LAB Router 的规划文档，
状态 **OPEN（后续任务，未授权执行）**。

**必须先解决的冲突**：文档 §4.6 / §5 / §6 的 JWT / OAuth2 / API Key / Vault 密钥管理
与铁律「本地个人研究使用：禁止加锁 / 访问令牌 / 鉴权入口」**直接冲突**，落地时必须改写为
无鉴权方案或整体舍弃，不得照搬。落地须走 `taskpacks/current/` 的 task-card / registry 流程
（参考 P1-C / P1-E 的 GOAL 34 先例）。

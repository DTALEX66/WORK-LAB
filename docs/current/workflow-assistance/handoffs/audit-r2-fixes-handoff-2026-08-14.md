# R2 云端重审计修复批次交接（2026-08-14）

日期：2026-08-14
范围：R2 审计报告（WORK-LAB-CLOUD-REAUDIT-2026-08-14-R2）第一批~第三批修复
合并：PR #97（真值/安全门禁）、#98（composition root 第一接线）、#99（watermark 表名）、#100（退役安全增量）、#101（退役文件删除）
基线：`6c6ae8a` → `6ee4a73`（本交接时 HEAD）

## 1. 已交付（可验证证据）

| 批次 | 内容 | 验证 |
|---|---|---|
| 第一批（PR #97） | P0-8 Guard 前缀绕过（_quoted_full_path + fail-closed）；P0-3 executions 一维 + token null/UNKNOWN + validator 深查；P0-4 normalizeV3 mode 取自 transport + SSE 命名事件 + eventsUrl；P0-7 canary exit 1 + exact-sha gate required | 25+23+16+11+10 tests；JS 45+4；gate 34 |
| 第二批第一接线（PR #98） | composition_root.py（load_approved_index + build_v3_snapshot）；canonical_store +5 读方法；sidecar /api/v1/snapshot 返回真 v3 + SseRevisionHub SSE + live-gate verdict + eventsUrl 回填 | 763 tests；live curl v3+OFFLINE+null；SSE 命名事件 |
| 第三批退役（PR #100/#101） | 前端死代码（dashboardEndpoint 删除）；Tauri 拒绝 /api/dashboard；ObserverStore→v3；check_5 迁移 v3；README v3-only；observer_dashboard/observer_canonical 文件删除；allowedWrites 移除 | 763+38+JS45+4；gate 34；convergence 8/10 claimable |

## 2. 错误经验（详见 error-fixes-2026-08-14-r2.md / Error Ledger ERR-055~060）

- Guard：Windows POSIX 路径 drive 映射错 + 正则双匹配 → 文本边界比较 + 引号向后探测
- zizmor Docker action input 失效 → pipx
- schema 升级四方同步（JSON/schema/verifier/test）
- SQL 表名核对；删除依赖保留 fail-closed；验证脚本自身 bug；gh merge graphql 瞬断重试

## 3. 剩余事项（未完成 / 环境受限，诚实边界）

```text
WORKER_SCHEDULER_BRIDGE: R2 第二批第二接线（composition_root.build_scheduler_bridge +
                        durable_worker L227/L233 两行 + adapter 注册）——需真实
                        Hermes/Codex 会话验证 evidence 写入，未做
DUAL_PROJECT_CANARY:    R2 第四批——WORK-LAB + 一个真实 OS 项目注册为批准
                        ProductProject（真实库已有 work-lab + open-design-assistance
                        两行），未批准前不收集
COLLECTOR_THREAD_LEAK:  P1-1——CollectorScheduler daemon thread join(timeout) 不取消，
                        超时线程累积（5 次超时 1→6 线程）
PERF_HARDCODED_PATH:    P1-2/3——perf_baseline.py 仍硬编码 D:\All projects\WORK-LAB
                        （canary_runner 已修自引用根）
WLGM_TASKPACK_IN_GIT:   P1-6——WLGM-000~240 权威任务包仍在 .project-local/desktop-attachments/
                        未纳入 Git tracked（50-taskpacks/ 无对应文件）
OBSERVER_EVENT_ADAPTER: observer_event.py / observer_projection_adapter.py 仅测试引用，
                        退役清单列为可删（未删，保留）
TAURI_RUST_DESCRIPTOR:  Rust 侧仍不读 endpoint descriptor（Python sidecar_endpoint.py
                        已实现+测试）；编译 PASS（本机 toolchain 已装）
EXACT_SHA_MAIN_CI:      post-merge main CI 每次 PR 后 success；独立 exact-SHA 证据见各 PR
```

## 4. 恢复顺序（按重要性）

1. P1-1 collector 线程泄漏（独立修复 + 线程数回归测试）
2. worker scheduler bridge（第二接线 PR，含 evidence 写入测试）
3. 双项目 canary（批准 open-design-assistance + WORK-LAB 双注册）
4. WLGM 任务包纳入 Git tracked（P1-6）
5. perf_baseline 自引用根（P1-2/3）
6. observer_event/adapter 清理（可选）

## 5. 关键文件

- `scripts/workflow/composition_root.py`（新，唯一组合根）
- `scripts/workflow/sidecar.py`（v3 端点 + SseRevisionHub）
- `scripts/workflow/snapshot_api.py` / `snapshot_validator.py`（真值修复）
- `scripts/workflow/canonical_store.py`（+5 读方法 + watermark 修复）
- `scripts/workflow/canary_runner.py` / `run_quality_gate.py`（真退出码 + required 语义）
- `bin/hermes-project-terminal-guard.py`（P0-8 前缀绕过修复）
- `30-observer/work-lab-observer/src/observer_store.py`（v3 rebuild）
- 文档：`docs/workflow/error-fixes-2026-08-14-r2.md`、`docs/handoffs/audit-r2-fixes-handoff-2026-08-14.md`

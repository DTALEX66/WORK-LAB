# WORK-LAB Observer

WORK-LAB Observer 是严格只读的观测与证据层，负责从 Workflow Assistance 和 Open Design 的公开事件/Snapshot 生成可重建的派生 Projection。

## 当前阶段

这是 v2 架构迁移的只读运行时基础。当前已建立模块边界、事件契约、项目内 JSONL 持久化、重启 readback、Projection 重建和结构验证；不迁移 Tauri UI、不读取凭据/Prompt/Response/Session，也不提供任务执行、批准、配置应用或 Git 写入入口。

## 允许的能力

- 读取公开的版本化事件和 Snapshot；
- 写入 Observer 自己的缓存、事件索引、Projection 和报告；
- 展示 source/coverage/quality/evidence 状态；
- 在 Observer 数据损坏后重建派生 Projection。

下层持久化入口为 `src/observer_store.py`。调用时必须同时传入
`project_root` 和 `project_root/.hermes/task-runtime/observer`；它会解析并严格比较
两者，拒绝同名外部目录、symlink/junction 越界目录和非 Git 项目根。它写入
Observer-owned JSONL，并在读取时重新执行 schema、敏感字段和重复 event ID 校验。

`src/observer_evidence.py` 提供一个受控跨模块投影入口：只接受 Workflow
Evidence Envelope 与 Open Design benchmark registry 的脱敏摘要，写入
Observer-owned normalized events；原始 payload、brief 和 evidence body 不会进入
Observer store，只保留 source digest 与受控 evidence references。它不修改两个
来源模块的权威状态，也不执行审批或晋级。

## 禁止的能力

- 修改 Workflow Registry、Task Ledger、Open Design Registry 或项目源码；
- 执行、暂停、恢复、重试、取消或批准任务；
- 应用配置、写入 Git/GitHub 或调用外部 mutation API；
- 读取 Secret、Cookie、认证数据库、完整 Prompt/Response、私密 Memory 或 Session DB。

## 验证

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/verify_observer_skeleton.py
PYTHONDONTWRITEBYTECODE=1 python tests/test_observer_skeleton.py
PYTHONDONTWRITEBYTECODE=1 python tests/test_observer_evidence.py
```

# WORK-LAB Observer

WORK-LAB Observer 是严格只读的观测与证据层，负责从 Workflow Assistance 和 Open Design 的公开事件/Snapshot 生成可重建的派生 Projection。

## 当前阶段

这是 v2 架构迁移的兼容骨架。当前只建立模块边界、契约和结构验证，不迁移 Tauri UI、不读取凭据/Prompt/Response/Session，也不提供任务执行、批准、配置应用或 Git 写入入口。

## 允许的能力

- 读取公开的版本化事件和 Snapshot；
- 写入 Observer 自己的缓存、事件索引、Projection 和报告；
- 展示 source/coverage/quality/evidence 状态；
- 在 Observer 数据损坏后重建派生 Projection。

## 禁止的能力

- 修改 Workflow Registry、Task Ledger、Open Design Registry 或项目源码；
- 执行、暂停、恢复、重试、取消或批准任务；
- 应用配置、写入 Git/GitHub 或调用外部 mutation API；
- 读取 Secret、Cookie、认证数据库、完整 Prompt/Response、私密 Memory 或 Session DB。

## 验证

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/verify_observer_skeleton.py
PYTHONDONTWRITEBYTECODE=1 python tests/test_observer_skeleton.py
```

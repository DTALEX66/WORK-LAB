# WORK-LAB Observer

WORK-LAB Observer 是严格只读的观测与证据层，仅从 Workflow Assistance 的公开事件与脱敏 evidence envelope 生成可重建的派生 projection。

## Boundary

- 只读读取公开事件、SSE 或等价快照；不执行任务、不写回 Ledger、不批准动作、不触发发布；
- 只持久化在项目 `.hermes/task-runtime/observer/` 下的 Observer-owned event log；
- 不读取 Prompt/Response 正文、凭据、Cookie、auth store、私钥或 provider state；
- Open Design 已迁移至 `DTALEX66/OPEN-DESIGN-Assistance`，本模块不再读取、投影或维护其事件。

## Verification

Run from the repository root:

```text
python 30-observer/work-lab-observer/tests/test_observer_runtime.py
python 30-observer/work-lab-observer/tests/test_observer_evidence.py
python 30-observer/work-lab-observer/tests/test_observer_store.py
```

# 知识迁移试点报告（TP-20260819 §12 · 2026-08-19）

> 状态：**NOT_EXECUTED**——按任务包 §12，正式批量迁移前先迁移三个代表对象；未通过试点验收不得批量迁移。

## 试点对象（待执行）

| # | 对象 | 来源 | 要求 |
|---|---|---|---|
| 1 | WORK-LAB 治理规则 | WORK-LAB（如 release-policy）| 原始路径/哈希/来源/Rights/Candidate ID/回执/回读/编译引用/哈希关系/回滚 |
| 2 | DESIGN-LAB MethodCard/Rubric | DESIGN-LAB | 同上 |
| 3 | 外置设计资料 SourceRecord | Design assets | 同上（大原件外置）|

## 通过条件（满足才允许批量）

1. ArcheAxis 可回读
2. WORK-LAB/DESIGN-LAB 通过引用继续使用
3. 原始资料未丢失
4. 权威关系明确
5. 回滚成功

## 当前阻塞

- ArcheAxis Candidate 提交/回读 API 尚未完成联邦契约化（AA-P0-002 进行中）
- 试点需 ArcheAxis 侧就绪后执行

## 结论

迁移试点 BLOCKED（依赖 ArcheAxis 知识 API 完整）。**未做任何迁移**，遵守 §16.10（全量反向迁移需人工批准）。
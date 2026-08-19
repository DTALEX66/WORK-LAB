# WORK-LAB 任务包（TP-20260819 联邦 · WORK-LAB 部分）

> 来源：TP-20260819-TRI-PROJECT-FEDERATION-V2（2026-08-19）。本文件为 WORK-LAB 执行子集。基线 main：7a8c90b（漂移自任务包基线 979ec88，增量=HERMES DSH 交接文档）。

## 状态约定

PASS / PARTIAL / FAIL / NOT_EXECUTED / BLOCKED。禁止用 DONE 代替证据状态。所有完成声明绑定 Exact SHA + 证据路径。

## WL-P0（修复任务）

- [ ] WL-P0-001 定位与注册表去硬编码：核心定位改为客户端/Harness/Agent/工具中立；外部软件名称迁入 software-registry/adapters/compatibility/evidence
- [ ] WL-P0-002 纠正专业能力越界：删除 domain-pack 所有权，改为通用 CapabilityPackageReference
- [ ] WL-P0-003 运行记忆降级：memory-record → runtime-context-record（TTL required，non-authoritative，source reference）
- [ ] WL-P0-004 Observer 写入否定测试：所有写路径测试验证 Observer 无法修改/批准/重试/回滚/改配置/执行/写 Secret
- [ ] WL-P0-005 配置控制面：六层模型 + 13 契约（SoftwareRegistrationV1 等）+ 迁移 + Diff/Apply/Readback/Drift/Rollback

## WL-P1

- [ ] WL-P1-001 当前证据真实性：重新生成 CURRENT_STATE，不得以 live_readback not-run 声称完成
- [ ] WL-P1-002 仓库减重：Git 对象/LFS/大文件体积报告，DSH 外置，不自动历史重写

## WL-OSS（开源组件 PoC）

- [ ] WL-OSS-001 chezmoi 适配评估（不退化 dotfiles 管理器）
- [ ] WL-OSS-002 SOPS Secret Adapter（内存解密/无明文/密钥轮换）
- [ ] WL-OSS-003 OPA 策略试点（三类规则，双跑对比）
- [ ] WL-OSS-004 OpenTelemetry（统一 Trace/Metric/Log Envelope，Observer 只读）
- [ ] WL-OSS-005 Langfuse（可选 LLM 观测，默认不发正文）
- [ ] WL-OSS-006 Dagger（Exact-SHA 构建测试，桌面任务不强行容器化）
- [ ] WL-OSS-007 Renovate（默认报告/待批准，禁止 automerge）
- [ ] WL-OSS-008 拒绝整体替代（Backstage/Temporal/Kestra 只做子系统）

## 联邦契约（§6）

- [ ] WORK-LAB/00-governance/federation/（federation-registry.v1.json + federation-envelope.v1.schema.json + THREE_PROJECT_FEDERATION_CONTRACT.md）

## E2E 契约测试（§11）

- [ ] E2E-001 人类学习闭环 / E2E-002 直接设计辅助 / E2E-003 受治理设计生产 / E2E-004 配置闭环
- [ ] 15 失败路径 fixtures

## 知识迁移试点（§12）

- [ ] 3 对象试点（WORK-LAB 治理规则 / DESIGN-LAB MethodCard / 外置 SourceRecord）
- [ ] 通过条件：可回读/引用可用/原始不丢/权威明确/回滚成功

## 交付文件（reports/current/）

- CLOUD_BASELINE / FEDERATION_MIGRATION_REPORT / EXACT_SHA_VERIFICATION / OPEN_SOURCE_ADOPTION_REPORT / CONTRACT_CONFORMANCE_REPORT / REMAINING_HUMAN_GATES
- CONFIGURATION_INVENTORY.json / CONFIGURATION_MIGRATION_READBACK.json / SOFTWARE_COMPATIBILITY_MATRIX.md / OBSERVER_READ_ONLY_PROOF.json

## 人工批准点（§16）

commit/push/PR/merge/release/迁移/Secret/保护规则/历史重写——均需人工批准。
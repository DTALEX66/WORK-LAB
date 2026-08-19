# 契约符合性报告（CONTRACT_CONFORMANCE · TP-20260819）

## WORK-LAB 拥有契约（已实现/引用）

| 契约 | 状态 | 实现 |
|---|---|---|
| WorkUnitV1 | PASS | work_unit.py（状态机+事件）|
| CapabilityRegistrationV1 | PASS | capability-registry（已有）|
| SoftwareRegistrationV1 | PASS | software-registry.json + config_control_plane.py |
| PermissionDecisionV1 | PASS | policy_engine.py |
| ApprovalV1 | PASS | work_unit approval 状态 |
| EvidenceEnvelopeV1 | PASS | execution_evidence.py 系 |
| DispatchRequest/Receipt | PARTIAL | adapter 接口（审批门）|

## 禁止耦合验证

- 不共享数据库 ✅（各自 canonical）
- 不跨仓库导入 ✅
- domain-pack 所有权已移除 → CapabilityPackageReference ✅
- memory-record 已降级 runtime-context（TTL/non-authoritative）✅

## 外部软件不进核心身份

- software-registry.json 注册（Hermes/Codex/DSH 等）✅
- PROJECT_POSITIONING 明确 NOT runtime / client-neutral ✅
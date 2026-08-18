# 三项目分层架构决策（v2 修正版 · 基于 GitHub 权威定位）

> 状态：权威决策。基于三个项目 GitHub 定位原文核实后重写，取代旧版。审计见 `00-governance/THREE_PROJECT_LAYERING_AUDIT.md`。

## 1. 问题背景

三个项目在知识库 + Agent + 模型 + 视觉方向存在重复建设风险，需收敛分层，消除重复。

## 2. 三个项目 GitHub 权威定位（锁死）

| 项目 | 权威定位 | 关键约束 |
|---|---|---|
| ArcheAxis-Knowledge-OS | local-first, evidence-driven, bidirectional Human-AI Learning & Trusted-Knowledge Workspace. NOT an Agent OS | 系统级人机双向学习与可信知识治理工作台 |
| WORK-LAB | client-neutral workflow control plane for the user's whole AI workflow | 明确 NOT agent runtime / model gateway / GPU 运行时 |
| DESIGN-LAB | 面向职业视觉设计的 AI 原生平台中立设计智能与生产能力实验室，Host-native，参考宿主 Open Design | 不重建画布/编辑器/模型网关/SaaS |

### 2.1 WORK-LAB 定位关键澄清（v1 错误）

WORK-LAB 是控制平面（control plane），不是运行时（runtime）。它管怎么管，不管怎么跑：
- Agent 执行 → 客户端（DSH 即 replaceable Agent Runtime、Hermes、Codex）
- 模型/GPU/视觉运行时 → 宿主（Open Design 等）
- WORK-LAB 通过 Adapter 治理客户端与宿主，但不拥有、不部署运行时

## 3. 目标与非目标

目标：三项目唯一职责、ArcheAxis 唯一知识真源、WORK-LAB 控制平面、DESIGN-LAB 领域智能、消除重复、建立双向闭环。
非目标：不合并、不把 ArcheAxis 改 Agent OS、不把 WORK-LAB 改运行时、不定义 API 契约（后续 RFC）。

## 4. 约束与不变量

1. 唯一知识真源：WORK-LAB/DESIGN-LAB 不自建知识库，走 ArcheAxis API。
2. 唯一治理权：candidate→review→verified 由 ArcheAxis 独占。
3. 人机双向不可偏废。
4. WORK-LAB 不拥有运行时（Agent/模型/视觉归客户端与宿主）。
5. DESIGN-LAB 不建基础设施（不做 RAG/模型管理/Agent 运行时）。

## 5. 最终架构：知识/控制/领域 三层 + 横向运行时

领域智能层 DESIGN-LAB（设计判断，宿主 Open Design）
   ↓ Adapter 接入宿主
控制层 WORK-LAB（配置投影 + 工作流治理 + 只读观测，NOT runtime）
   ↓ 知识读写走 API
知识层 ArcheAxis（人机双向学习 + 可信知识，NOT Agent OS）

横向（被管理对象，非分层成员）：
  Agent Runtime = 客户端 DSH/Hermes/Codex
  模型/GPU/视觉运行时 = 宿主 Open Design
  由 WORK-LAB 治理，不归 WORK-LAB 拥有

## 6. AI 侧调用闭环

需求 → WORK-LAB 任务治理（归属/路径/边界/审批）→ 客户端 Agent 执行 → DESIGN-LAB 专业判断（宿主内）→ ArcheAxis 查询知识 → 宿主工具执行 → 结果回写 Candidate → ArcheAxis 治理 → 人机双向进化

## 7. 职责边界

### 7.1 ArcheAxis（知识根基）
保留：人类学习链（摄入/结构化/课程/练习/FSRS 复习/掌握/Teach Back）、AI 知识服务（Knowledge/Memory/Evidence API）、双向进化、受限受治理执行 tracer。
删除：通用 Agent Runtime、多 Agent 调度、自治工作流（NOT Agent OS）。

### 7.2 WORK-LAB（控制平面）
保留：全局配置层（Rules/Skills/MCP/Memory/Policy 投影）、工作流治理（task-pack）、只读观测、Adapter 契约。
删除：运行时误解（Agent/Model/Vision Runtime 从未属于 WORK-LAB）；专业知识库→ArcheAxis；设计规则→DESIGN-LAB。

### 7.3 DESIGN-LAB（领域智能）
保留：设计规则/方法/六能力域、审美判断/质量/预检/交付/证据。
删除：通用 RAG→ArcheAxis；模型管理→宿主；Agent 基础设施→客户端+WORK-LAB 治理。

## 8. 视觉能力归属（修正）

| 类型 | 归属 |
|---|---|
| 视觉运行时 | 宿主（Open Design）|
| 视觉记忆 | ArcheAxis |
| 视觉智能 | DESIGN-LAB |

## 9. Agent 归属

| 项目 | 角色 |
|---|---|
| 客户端 DSH/Hermes/Codex | System/执行 Agent |
| WORK-LAB | 不拥有 Agent，只治理 |
| ArcheAxis | Knowledge Service（非 Agent）|
| DESIGN-LAB | Domain 能力（非通用 Agent）|

## 10. ArcheAxis 红线（与 GitHub 一致）

1. 人机双向不可偏废；2. 独立系统非 WORK-LAB 模块；3. 唯一知识真源=唯一治理权；4. NOT an Agent OS（保留受限受治理 tracer）。

## 11. 优先级：ArcheAxis > WORK-LAB > DESIGN-LAB

## 12. 落地建议

1. 定接口契约（ArcheAxis 暴露 Knowledge/Memory/Evidence/Experience/Learning API）。
2. WORK-LAB 做减法：保持控制平面，知识库迁移 ArcheAxis。
3. DESIGN-LAB 做减法：去 RAG/模型管理，知识走 ArcheAxis，执行走宿主。
4. ArcheAxis 做加法：人类学习链完整 + candidate 审核闭环。
5. 视觉/模型运行时归宿主，WORK-LAB 治理不部署。
6. 跑通一个双向闭环验证。

## 13. 结论

ArcheAxis 管可信知识+人机双向学习，WORK-LAB 管 AI 怎么被治理（控制平面），DESIGN-LAB 管设计怎么判断（领域智能）。运行时横向归客户端与宿主。不合并、不都做 Agent、不都做知识库、不把 WORK-LAB 当运行时。
# 三项目分层架构决策（v3 · 知识全量归档 + 双转化器）

v3 核心修正：一切可转化知识（规则/治理/工作流/设计方法/事实/经验）统一归档 ArcheAxis 为唯一真源；WORK-LAB 与 DESIGN-LAB 是知识的调用者与转化器，不再各自持有知识。取代 v2 的三分法。

## 1. 架构总原则

任何能被转化的知识，都归档到 ArcheAxis。规则、治理规范、工作流定义、设计方法、Rubric、事实、经验、Lesson 本质都是可复用知识，统一由 ArcheAxis 治理为唯一真源，后两个项目通过 API 调用并转化。

## 2. 三层（知识 / 转化 / 执行）

### 第一层 ArcheAxis（唯一知识真源 + 治理，NOT Agent OS）
- 归档一切可转化知识：事实、证据、案例、经验、Lesson、规则、治理规范、工作流定义、设计方法、Rubric、材料规范、客户反馈
- 承载对象：Knowledge Unit / Machine Knowledge Unit / Learning Artifact / Lesson（candidate 到 review 到 verified）
- 提供 API：Knowledge / Memory / Evidence / Reasoning / Learning
- 边界：只存知识定义，不存可执行载体（skill 实现代码、MCP 插件、运行时）

### 第二层 转化器（调用 + 转化，不持有知识）
- WORK-LAB（控制转化器）：把 ArcheAxis 知识（规则/工作流/治理规范）转化为客户端可执行配置投影，做工作流治理与只读观测；是控制平面，不是运行时，不自建知识库
- DESIGN-LAB（设计转化器）：把 ArcheAxis 知识（设计方法/Rubric/案例/规范）转化为设计判断与专业能力，运行在宿主 Open Design 内；不建通用 RAG，不存设计知识

### 第三层 执行（宿主 + 客户端）
- Agent 执行 = 客户端（DSH/Hermes/Codex）
- 模型/GPU/视觉运行时 = 宿主（Open Design 等）
- 由 WORK-LAB 通过 Adapter 治理，不归 WORK-LAB 拥有

## 3. 知识流转闭环

人类学习 / AI 执行产出 到 Candidate 归档 ArcheAxis 到 人工审核 到 verified 知识 到 WORK-LAB 转化（规则到配置投影）+ DESIGN-LAB 转化（方法到设计判断）到 宿主/客户端执行 到 结果回写 Candidate 到 治理 到 人和 AI 复用 到 双向进化

## 4. 归属速查

| 内容 | 归属 |
|---|---|
| 事实/证据/案例/经验/Lesson | ArcheAxis 唯一真源 |
| 规则/治理规范/工作流定义 | ArcheAxis 存定义，WORK-LAB 转化执行配置 |
| 设计方法/Rubric/材料规范 | ArcheAxis 存定义，DESIGN-LAB 转化设计判断 |
| skill 实现代码/MCP 插件/运行时 | 机器资产，WORK-LAB 部署（规范定义归档 ArcheAxis）|
| Agent 执行/模型/视觉运行时 | 客户端 + 宿主，WORK-LAB 治理 |

## 5. ArcheAxis 红线（不变）

1. 人机双向不可偏废 2. 独立系统非模块 3. 唯一知识真源等于唯一治理权 4. NOT an Agent OS（只存知识定义不存执行）

## 6. 落地顺序

1. 定 ArcheAxis 知识 API 契约（Knowledge/Memory/Evidence/Learning）
2. WORK-LAB 减：现有知识库/规则/模板归档 ArcheAxis，只留转化投影 + 治理 + 观测
3. DESIGN-LAB 减：设计知识归档 ArcheAxis，只留转化判断 + 宿主执行
4. ArcheAxis 增：补 Machine Knowledge Unit（承载规则/方法）+ candidate 审核闭环
5. 跑通一个双向闭环：知识到转化到执行到回写到治理到复用

## 7. 结论

ArcheAxis 是所有可转化知识的唯一真源与治理者；WORK-LAB 和 DESIGN-LAB 是知识的调用者与转化器（一个转成控制，一个转成设计判断）；执行在宿主与客户端。人和 AI 共享同一份知识底座，双向进化。
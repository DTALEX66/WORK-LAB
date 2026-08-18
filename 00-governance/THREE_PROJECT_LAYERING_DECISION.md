# 三项目分层架构决策（v3.1 · 定位锁定版）

本文档锁死三项目分层。核心不变式：ArcheAxis 的定位永不漂移——它一直是、未来蓝图也始终是【双向人类-到-AI 的重型学习系统级项目】，不是知识归档库、不是被调用的知识后端、不是 Agent OS。

## 1. ArcheAxis 定位（最高优先级，不可漂移）

ArcheAxis Knowledge = local-first, evidence-driven, bidirectional Human-AI Learning & Trusted-Knowledge Workspace. NOT an Agent OS.

它是系统级【人机双向重型学习系统】。同一份可信知识，人学得更深，AI 用得更准：
- 人类端（重型学习链）：资料摄入、结构化、课程笔记、练习、FSRS 复习、掌握、应用、Teach Back、知识迁移——这是人类重型学习系统，不可弱化
- AI 端（知识使用链）：检索、上下文供给、任务支持、经验积累、Lesson 回写
- 双向反馈：人的学习产出与 AI 的任务产出都先成 Candidate，经治理后共同演进知识底座

未来蓝图（锁定重型学习系统级）：docs/truth/FROZEN_EXECUTION_BASELINE（H0-H10）、docs/blueprint/SYSTEM_MASTER_BLUEPRINT_V2。这个重型学习系统级定位不随任何分层调整而漂移。

## 2. 架构总原则（知识全量归档是机制，不是定位）

任何能被转化的知识（规则/治理规范/工作流定义/设计方法/Rubric/事实/经验/Lesson）统一归档 ArcheAxis 治理为唯一真源。这是 ArcheAxis 的治理机制之一，服务于它的双向学习系统定位——不是把 ArcheAxis 降级为知识库。

WORK-LAB 与 DESIGN-LAB 是知识的调用者与转化器，不各自持有知识。

## 3. 三层（学习系统 / 转化 / 执行）

### 第一层 ArcheAxis（人机双向重型学习系统，NOT Agent OS）
- 核心：人类学习链 + AI 使用链 双向同等重要，共享同一知识底座
- 知识全量归档：事实、证据、案例、经验、Lesson、规则、治理规范、工作流定义、设计方法、Rubric、材料规范
- 承载对象：Knowledge Unit / Machine Knowledge Unit / Learning Artifact / Mastery Signal / Lesson（candidate 到 review 到 verified）
- 提供 API：Knowledge / Memory / Evidence / Reasoning / Learning，供后两层调用
- 边界：只存知识定义，不存可执行载体（skill 实现代码、MCP 插件、运行时）

### 第二层 转化器（调用 + 转化，不持有知识）
- WORK-LAB（控制转化器）：把 ArcheAxis 知识（规则/工作流/治理规范）转化为客户端可执行配置投影，做工作流治理与只读观测；控制平面，非运行时，不自建知识库
- DESIGN-LAB（设计转化器）：把 ArcheAxis 知识（设计方法/Rubric/案例/规范）转化为设计判断与专业能力，运行在宿主 Open Design 内；不建通用 RAG，不存设计知识

### 第三层 执行（宿主 + 客户端）
- Agent 执行 = 客户端（DSH/Hermes/Codex）
- 模型/GPU/视觉运行时 = 宿主（Open Design 等），由 WORK-LAB 通过 Adapter 治理

## 4. 双入口 + 知识流转闭环

人类用户两个入口：1) 直接在 ArcheAxis 中学习和治理（人类学习链）；2) 通过 WORK-LAB/DESIGN-LAB 使用 AI 能力（AI 使用链）。两链共享同一知识底座。

闭环：人类学习 / AI 执行产出 到 Candidate 归档 ArcheAxis 到 人工审核 到 verified 到 WORK-LAB 转化（规则到配置）+ DESIGN-LAB 转化（方法到判断）到 宿主/客户端执行 到 结果回写 Candidate 到 治理 到 人和 AI 复用 到 双向进化

## 5. 归属速查

| 内容 | 归属 |
|---|---|
| 事实/证据/案例/经验/Lesson | ArcheAxis 唯一真源 |
| 规则/治理规范/工作流定义 | ArcheAxis 存定义，WORK-LAB 转化执行配置 |
| 设计方法/Rubric/材料规范 | ArcheAxis 存定义，DESIGN-LAB 转化设计判断 |
| skill 实现代码/MCP 插件/运行时 | 机器资产，WORK-LAB 部署（规范定义归档 ArcheAxis）|
| Agent 执行/模型/视觉运行时 | 客户端 + 宿主，WORK-LAB 治理 |

## 6. ArcheAxis 定位红线（最高优先级，不可漂移）

1. 人机双向不可偏废：人类重型学习链与 AI 使用链同等重要，不得把 ArcheAxis 窄化为 AI 记忆库或知识后端
2. 独立系统：有完整生命周期，不是 WORK-LAB/DESIGN-LAB 的模块
3. 唯一知识真源 = 唯一治理权：candidate 治理由 ArcheAxis 独占，人和 AI 产出都不能自动升级为事实
4. NOT an Agent OS：不做通用 Agent Runtime、多 Agent 调度、自治工作流；保留受限受治理执行 tracer
5. 未来蓝图锁定：重型学习系统级项目（FROZEN_EXECUTION_BASELINE H0-H10 + SYSTEM_MASTER_BLUEPRINT_V2），不随分层漂移
6. 受控调用边界：ArcheAxis P3 的受控调用 = 知识/学习资产的调用复用组合评估，不是 Agent/工具调用（后者归 WORK-LAB）
7. 受限探索边界：ArcheAxis P10 的受限探索 = 知识治理辅助的受限 tracer，不是通用 Agent 执行（守住 NOT Agent OS）
8. 设计研究边界：DESIGN-LAB 的 Research & Evidence = 设计领域研究（案例/合规/材料），通用知识研究归 ArcheAxis，设计研究的事实性知识归档 ArcheAxis 真源

## 7. 落地顺序

1. 定 ArcheAxis 知识 API 契约（Knowledge/Memory/Evidence/Learning）
2. WORK-LAB 减：现有知识库/规则/模板归档 ArcheAxis，只留转化投影 + 治理 + 观测
3. DESIGN-LAB 减：设计知识归档 ArcheAxis，只留转化判断 + 宿主执行
4. ArcheAxis 增：人类学习链完整 + Machine Knowledge Unit + candidate 审核闭环
5. 跑通双向闭环：知识到转化到执行到回写到治理到复用

## 8. 结论

ArcheAxis 是人机双向重型学习系统（定位不变、未来蓝图锁定），是一切可转化知识的唯一真源与治理者；WORK-LAB 和 DESIGN-LAB 是知识的调用者与转化器（一个转成控制，一个转成设计判断）；执行在宿主与客户端。人和 AI 共享同一份知识底座，双向进化，越用越强。
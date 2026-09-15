# WORK-LAB｜MONITORING-INTAKE-20260915 未完成任务登记

登记日期：2026-09-15。性质：**AUDIT_RECOMMENDATION_ONLY 登记，不是新的权威 TaskPack**，不授权安装、付费、修改生产或替换。
来源：桌面 07_WORK-LAB_工作区接入交接.md / 01_审计报告与三项目融入建议.md / 05_附件完整性与工作簿审计.json（MONITORING-INTAKE-20260915）。
原始上传附件 SHA-256 以 05 JSON `input_files` 为准（7 文件含 xlsx 工作簿）；完整原任务映射见 03_43条原任务_去重映射.json（未上传，UPLOAD_REFERENCE_ONLY）。

## 0. 治理状态

CODEX / DSH / HERMES 三方治理任务**暂时告一段落**（用户 2026-09-15 声明）：
- DSH→Hermes ✅（763da68）· Hermes→Codex ✅（b4a18c4 / 2940586 / 7bee499 / fa9f312，双端一致 CI 12/12×2）
- 未做：Codex→DSH 段、DSH 对 Hermes 写入面的独立复核、工具执行层合成验收（沙箱 ACL 环境阻塞，需桌面重跑或授权 runner 访问 C:\Users\Default）
- 后续是否续段，等用户新指令；本登记不派工。

## 1. 事实核实（本地已验证，2026-09-15）

| 07 声称 | 核实结果 |
|---|---|
| radar_core blob=42e62052 | ✅ HEAD:services/radar/radar_core.py 完全一致（无漂移） |
| 根 AGENTS 仍含 10-workflow 旧路径 | ✅ L9（scope 根声明）+ L79（execution contract）仍在；`10-workflow/` 0 个 tracked 文件，磁盘仅 1 个陈旧 untracked `__pycache__/*.pyc` |
| services/radar/ 模块 | ✅ radar_core.py / radar_scoring.py / auto_poc_routing.py 在册 |

注意：F04 上轮只修了 AGENTS L88 门禁命令路径；**L9/L79 根声明残留属于本登记的未完成任务**（本轮不擅改 AGENTS，治理已告段落；修改需下次治理授权）。

## 2. WORK-LAB 未完成候选（按 01/07 分流，登记不派工）

| ID | 内容 | 边界 | 状态 |
|---|---|---|---|
| WL-R01 | 用本批上传作离线 Radar 样本，在现有 radar_core 上补**证据/差分/覆盖**，不新建后台 | DeepSeek 结构/离线 | 未做（最高直接价值入口） |
| radar_core 静态缺陷 | ① discover() first-writer-wins 丢更新 ② Candidate 缺省 0/false 混同 unknown 与 confirmed_false ③ StaticSourceAdapter.available() 混淆"合法空结果"与"源不可用" ④ 无价格时效/权益/规范版本/fits 结构化字段 ⑤ min_stars 排序不通用于模型/论文/标准 | 增量映射/sidecar，不推倒框架 | 未做 |
| WL-R02 / WL-R06 / W01 / W04 | 只查**实际在用**的 ACP/MCP/AG-UI 及模型别名；按提供方测 load/fork/cancel/perms；AG-UI 按子包破坏性变更核查锁文件与 imports；codex-acp 实现版本≠协议版本 | DeepSeek 静态；Codex 联调 | 未做 |
| WL-R04 / WL-R05 / W03 | 假工具/假凭据/合成事件测越权拒绝、重复事件、并发与恢复；UNKNOWN 外部动作先对账；界面停≠进程停；托管拒绝≠放宽权限理由 | DeepSeek 受控；Codex 实机取消 | 未做 |
| WL-R07 / W07 | 模型/API 表改为带时效/供应方/币种/地域/计费模式的价格记录；未知费用不填 0；工作簿 4 项边界加固（小数调用次数、计价除数 0、语音负时长、无数据验证/表保护）→ 加固前不得当执行预算引擎 | DeepSeek 离线；真实 usage 需授权 | 未做 |
| WL-R03 | 运行状态四组对照：先旁路观察/确定性重放（tracelab 模式），收费四臂实验仅在必要时且需批准；不重建 TaskStore/TelemetryStore | 付费需批准 | 未做 |
| W05 / W06 / Bolt | Kimi 权益（订阅≠免费 API）、Agents API 可选执行器（本地任务状态/产物导出/费用边界保留）、Bolt 仅脱敏一次性原型 | 只读准备；真实接入需授权 | 未做 |
| 恒定约束 | Observer 保持只读；候选"值得 POC"不自动触发安装/写 TaskPack/PR/生产替换；W02 与 WL-R03 不混为一个因果实验；每实验初始预算 0 不改全局模型政策 | — | 约束 |

其他两项目（ArcheAxis Green 闭环、DESIGN-LAB 设计资产验收）不在本项目登记内，按 01 §8 各自边界。

## 3. 带病登记（与上述无关的既有项）

- 5 项既有 Windows 环境测试失败（test_machine_identity + test_workflow_governance portable-install 4 项）——基线复现，非补丁引入
- 14 个技能 `.bak` 备份删除——仍无授权
- 工具执行层合成验收 BLOCKED（沙箱 ACL，C:\Users\Default 权限 5）

## 4. 停止点

本登记**不构成派工、安装、付费或生产替换授权**；导入批准≠下载批准≠付费执行批准≠宿主控制批准≠生产替换批准。
下一步由用户决定：续治理段、启动 WL-R01 离线 Radar 样本链、或两者都停。

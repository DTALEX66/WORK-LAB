# WORK-LAB TOP-LEVEL AUTHORITY

**Authority ID:** `WORK-LAB-AUTHORITY-20261009-UI-PRIORITY`
**Repository:** `DTALEX66/WORK-LAB`
**Authority level:** TOP / NORMATIVE
**Decision:** 用户2026-10-09采纳新任务包、UI优先、旧任务有用并账/无用冻结归档、手机端不做且不建延后/冻结任务。
**Document delivery is not implementation:** 本轮产品代码NOT_EXECUTED。

## 1. Current authority and bootstrap

每次审计/执行先动态读取origin/main精确commit/tree，再读本文件、`.project/governance/project-authority-index.json`、AGENTS.md、
`.project/governance/taskpack-authority-index.json`指向的唯一CURRENT、`taskpacks/current/OPEN-TASK-REGISTER.md`及作用域机器合同。
优先级：最新明确用户决定 > 本文件 > project-authority-index > CURRENT/OPEN > AGENTS及作用域合同 > exact-SHA代码/CI/运行读回 > 冻结历史。
当前计划：`taskpacks/current/WORK-LAB-UI-PRIORITY-TASKPACK-20261009.md`。旧任务包不继续独立派工。
历史记录只在具体问题需要时读取；缺引用报告AUTHORITY_REFERENCE_MISSING，不从历史拼造新权威。

## 2. Product identity and boundaries

WORK-LAB是软件中立、本地优先的AI工作观测与配置治理工作台。
用户在外部AI软件执行项目；本方默认按项目观察参与软件、活动、阻碍、资源与新鲜度，不强制所有工作创建/派发/审批。
能力主线是源评价、许可依赖权限、用户选择目标、最小中立化、差异损失、目标验证、获准部署读回恢复与版本维护。
规则统一意图、适配原生形态，不统一覆盖字节。管理权按`config/config-ownership.json`声明，未知和用户provider/model/auth状态保留。

AAOS拥有完整知识生命周期、人的知识工作/研究/学习、AI学习资产、人机双向学习和长期项目记忆。
DESIGN-LAB拥有全品类专业设计、原生作品、设计专用内核及专业验收。Open Design客户端与DESIGN-LAB项目是不同身份。
WORK-LAB提供技术候选/示例/检查/反馈，不拥有对端知识可信决定、作品专业接受或真人学习评价。
三方独立运行与发布，直接/双边/多方按需协作；不建总控制器或本地知识/学习/课件主库。
本仓开发TaskLedger/单写者/门禁不自动成为被观察业务项目的使用义务。

## 3. UI-first current scope

新20261009两个包为当前范围输入；原件完整归档，执行提示和历史验证不额外授予权限。
唯一当前计划按WUI-00..WUI-20分解：先桌面首页/导航/组件/对象详情，再接真实数据、能力迁移、规则、诊断设置、兼容和验收。
五主要目的地是建议，不是永久页数测试；协作放对象详情；旧task/execution/evidence保留只读身份兼容。
手机端不做，OUT_OF_SCOPE，不设置手机端延后或冻结任务。原包17_mobile仅为归档素材。
main桌面与既有compact HUD分别保留；HUD不是手机端。React/TS/Vite + Tauri/Rust + Python + JSON Schema分工不换栈。
Observer与sidecar严格只读，不执行/apply/rollback/批准/重试或写业务状态；正常搜索筛选复制展开可用。
获准配置/资产写复用既有独立Control边界，服务端检查主体、范围、前态、版本、幂等、原生读回和恢复。
无全仓Rust重写、第二UI/运行时/TaskLedger/Usage真源；有效已实现功能与安全门保留。

## 4. Runtime and data truth

项目身份支持非Git、多目录/worktree及同名；参与软件集合及工作/健康/观测三轴不混。
断连不推出软件停止，无日志不判失败，turn_end不判项目完成；源/接收/可见时间、序列及last-good有明确限制。
默认最小字段白名单，不采集私人提示词/回复/工具载荷/完整子Agent轨迹；诊断按项目/问题/时间/保留范围授权。
Token/Credits/费用/额度/资源分开，真实0/缺失/不可计算分开；字段精度/完整性、增量累计/修订/重试fork去重守恒。
缓存输入占比按完整同口径总分子/总分母，请求命中率按可判断请求；缓存写入不是读命中，不造全局覆盖率。
受管软件仍遵守五维底线：官方唯一入口、GUI桌面可达、官方基准+声明overlay、按需精简不阻塞、用户原生任务级模型选择。
常态观测不调用LLM；单适配器故障局部，窗口/采集/原生软件生命周期分开。

## 5. Module, write and safety boundaries

规范模块由`.project/governance/module-ownership.json`确定：packages/client-neutral-core与apps/observer。
services/integrations/config/apps/token-monitor/scripts/tests是支撑面；现有Control服务不是新运行时。
一个write set一个writer，保护dirty修改；并行writer需要隔离worktree，跨模块按明确任务合同。
所有缓存/临时环境/日志在`.project-local/runs`，证据在`.project-local/artifacts`，持久文档在仓库声明位置。
Record原料根只读；E/F无exact path+operation授权禁止任何访问。不得读/打印/复制凭据、.env、认证库、私人session/memory。
不reset --hard/clean/force push/改Git历史，不擅自升级安装/改PATH/ACL/服务/全局配置或删除资产。
只管理声明字段，preserve_unknown=true；软件版本/路径/模型/CI动态核对，不把旧固定数字当现场事实。

## 6. Evidence, archive and delivery

证据等级NO_EVIDENCE/SIMULATED/SYNTHETIC/INTEGRATED/REAL；REAL需可核验身份、摘要/句柄、producer、observedAt与读回。
实现、受控测试、真实客户端、Windows/Tauri、人工专业接受、发布分别报告；build≠runtime、fixture≠REAL、push≠merge、merge≠installed。
必要fail/missing/skip/cancel不PASS。UNKNOWN不是0。技术通过不等于知识可信、设计接受、真人学会或工作效果。
旧任务逐行保留ID/状态/证据，并账不代表实现完成；无用旧规划冻结归档，不继续派工。原缺陷/失败不清零。
原字节快照：`taskpacks/history/UI-PRIORITY-CUTOVER-20261009/FROZEN-MANIFEST.json`；任务处置：`docs/current/ui-priority-20261009/LEGACY-TASK-DISPOSITION.json`。
原件包：`docs/history/owner-inputs/20261009/SOURCE-INTEGRITY.json`。不可变来源不改字节；更正旁置；有消费者的旧路径保留非执行兼容入口。
本轮授权文档/索引/任务归档与交接，产品实现NOT_EXECUTED。下一Agent仅按其具体用户Task Grant推进。
commit/push/PR/merge/release/安装/全局/跨项目/付费/发送分别判断；验证不自动授予这些权限。
main仍是唯一永久代码权威；正常短分支→PR→exact-SHA CI→review→merge，禁止直推绕过门禁。

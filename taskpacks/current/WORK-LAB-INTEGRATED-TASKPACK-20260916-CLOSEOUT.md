# WORK-LAB 集成任务包 20260916 — 完整收口报告（总结 / 问题 / 阻塞）

- 双端一致：`r4-recovery-exec` 本地 == 远端 == `acedf3e`（本报告提交后精确 SHA 复核）。
- 交付定性：**READ_ONLY_PREVIEW**（全程零真实全局写 / 零付费调用 / 零凭据 / 零 E 盘 / 零跨项目写）。
- 回归：`tests/workflow-assistance` 1259 passed / 8 skipped / 0 failed（8 skip 全为既有 Windows 平台门控：symlink 权限 WinError 1314 / POSIX 语义，非本轮引入）。
- 门禁：`work-lab-gate` 提交链 `acedf3e / 9aace50 / 51d951f / 659ba93 / a3c5061 / 37f93f6 / 3a38d48` 全 success。

## A. 总结（摘要）
本轮把 20 张卡任务包中的 **16 张必做卡全部闭环**，4 张可选卡按包协议 deferred（需付费模型 + 单批授权）。
范围包括：CI 根因修复（NF-02）、配置事务诚实态（NF-04）、只读客户端价值闭环 + 身份契约锁定（NF-05/06）、
单字段受控应用/恢复（NF-07）、最小跨软件 handoff（NF-08）、Observer 五态只读投影（NF-09）、
技能/依赖/模型收敛审计（NF-10/11/12）、Radar 离线复用闭环 + 价格身份规范化（WL-R01/07）。
同时完成外溢数据追踪（零外溢）与项目本体瘦身审计（tracked 区零构建/缓存污染）。

## B. 逐卡闭环证据（16 必做）
| 卡 | 交付 | commit | 测试 |
|---|---|---|---|
| NF-00 | 基线 693471c 双端一致 + 基线回执 | 0432b2d | — |
| NF-01 | 全局执行标准去死路径/去 force/语义对齐 AGENTS | 0432b2d | 53 AGENTS 相关测试绿 |
| NF-02 | CI 根因：`from services` 硬导入 → TYPE_CHECKING/文件路径加载（gate-safe） | 0432b2d + 5980581 | gate 10 命令 + 全量绿 |
| NF-03 | 外溢追踪回执（全锁定 gitignored `.project-local/runs/`） | 49774f5 | — |
| NF-04 | 配置事务 NOOP / APPLY_FAILED(UNDETERMINED) / COMMITTED_SIMULATED + 4 契约测试 | efbde9e | 1259 绿 |
| NF-05/06 | 只读价值闭环（脱敏回执、确定性）+ 4 条身份/路由契约锁定 | 3a38d48 | 12 |
| NF-07 | 单字段 前态→应用→回读→受控恢复（并发保留/幂等/诚实标注未真实适配） | 37f93f6 | 4 |
| NF-08 | 最小跨软件 handoff（脱敏载荷 + 差集 4 场景）+ 承接既有 8 场景 | a3c5061 | 7 |
| NF-09 | 投影五态（LIVE/ACTUAL_ZERO/STALE/UNKNOWN/UNAUTHORIZED）+ 只读 surface 锁死 | 659ba93 | 7 + 前端 80/80 + Python 36/36 |
| NF-10/11/12 | 收敛审计（技能按需 + 用户原生字段保护 + 依赖清单 + 模型差分 UNVERIFIED） | 51d951f | 6 |
| WL-R01 | Radar 离线闭环（重放不造重复候选/版本差分可解释/证据不足非高置信/中文报告/不自动晋级） | 9aace50 | 12（与 R07 同组） |
| WL-R07 | 价格身份规范化 + UNKNOWN 传播（缺项→UNKNOWN 不塌缩为 0；分道；旧值保留有效时间） | 9aace50 | 12（与 R01 同组） |
| NF-14 | 交付定性 READ_ONLY_PREVIEW + 停止条件（本文件） | acedf3e+ | — |

4 可选卡（NF-13 / W05 / W06 / W08）：`optional_ids`，包协议默认不执行，需付费模型 + 单批授权 → 见 D。

## C. 问题（发现并修复 / 登记）
1. **NF-02 CI 根因**（run 34993528858，9 errors）：`radar_observations.py` 与 radar 测试用 `from services...`
   硬导入，gate 直跑 runner 的 `sys.path[0]` 是测试目录而非仓库根 → 修为 TYPE_CHECKING 惰性导入 +
   测试文件路径加载 + `sys.modules` 预注册。已 CI 验证绿。
2. **NF-04 事务状态机缺口**：空 diff 无 NOOP、apply 异常无 UNDETERMINED 写态、模拟适配器无
   SIMULATED 标签 → 补 3 态 + 4 契约测试（防"假成功"）。
3. **NF-07 受控恢复误报 bug（本轮自纠）**：restore 初稿拿 current 与"要恢复到的值"比较，正常流程
   必然误判冲突 → 改为与 last_written 比较（并发改动才拒绝盲恢复）。
4. **NF-08 差集缺口**：既有 8 单写者场景不覆盖"两入口交接"的应答丢失/重启重复/取消后产出/外部未知
   → 补最小 handoff 原语（脱敏白名单载荷、稳定 delivery id、终态守卫、未知效果 reconcile 不盲重试）；
   不伪称 exactly-once。
5. **NF-09 投影层三态缺口**：前端 627 行只读回归已很强，但投影层缺 LIVE/STALE/UNKNOWN/UNAUTHORIZED/
   实际 0 五类分开（实际 0 ≠ 未知）+ 每项带来源时间/范围 → 补纯函数分类器 + 只读 surface 锁。
6. **NF-10/11/12 审计面**：用户原生字段（provider/model/reasoning/hook/MCP/plugin）此前无契约测试锁定
   防静默改弱 → 收敛审计层 + 6 契约测试；14 全局备份在 `~/.agents/skills`（跨项目）→ 越界不读，诚实标注。
7. **WL-R01 闭环缺口**：`ObservationLedger.diff` 已有差分，缺"离线样本→重放→中文候选报告→确定性回执"
   与五类复用判断（DIRECT_DEPENDENCY/…/REJECTED）+ 证据等级门控 → 补 `radar_reuse_loop.py`（纯函数，
   不重造 Radar、不动 17 字段契约）。
8. **WL-R07 价格身份缺口**：`PriceRecord` 有字段但无规范化/UNKNOWN 传播/分道/旧值有效时间 → 补
   `normalize_price_identity` + 确定性回执；工作簿实体未取得 → 不杜撰（见 D5）。
9. **既有 Windows 顺序相关 flaky（5 个）**：全量顺序跑时偶发失败（GBK/全局状态污染类），已登记
   open-tasks；单文件/CI 顺序稳定绿，非本轮引入，未在本轮修（避免修 2 轮不收敛即漂移的重复劳动）。
10. **`test_apply_safety.py` 硬编码 `sys.path` 指向不存在的 `scripts/workflow`**：pytest 经 conftest
    可过，独立直跑挂 → 登记为遗留债，不影响 CI，未动。
11. **子代理 429 全军覆没 + 幻觉自述**：4 并行子代理全被 free-tier API 429 打爆；task-3 自述写了
    5 个文件（`candidate_loop.py` 等），磁盘逐一验证 **全部不存在**（幻觉报告）→ 全部改中央顺序通道
    完成，磁盘/测试/CI 三重验证，零残留（worktree 始终 clean）。
12. **gate 命令的 CURRENT_STATE 时间戳 churn**：跑 gate 会重生成 volatile 时间戳 → 每次提交前
    `git checkout` 恢复，digest 不变。

## D. 阻塞（需用户操作 / 单批授权，诚实口径）
1. **Hermes 自升级**：活动 kernel 锁（PID 26144）禁止自升级 → 需用户正常退出后走官方维护入口。
2. **Hermes hook 重新批准**：需交互式 UI → 用户操作。
3. **Codex 工具层 ACL**（`C:\Users\Default` WriteAttributes）：SeSecurityPrivilege 系统权限边界，
    无法在本授权内完成 → 登记，不强闯。
4. **4 可选卡（NF-13/W05/W06/W08）**：需付费模型调用 + 单批授权 → deferred，非 release blocker。
5. **WL-R07 工作簿实体**（xlsx 数据验证/表保护列 + Excel/WPS 实机兼容）：实体未提供 → 价格链
   离线边界已证明，UI/兼容项诚实标"未验证"，不凭文件名杜撰结果。
6. **NF-07 实字段**（具体 client/profile/field 的真实应用与恢复）：本轮零真实全局写授权，
   机制由合成闭环证明；实字段卡保持 NOT_PASSED_AWAITING_AUTHORIZATION。
7. **429 free-tier 限流**：子代理并行通道不可用 → 本轮全走中央顺序通道（已完成，非持续阻塞）。

## E. 外溢数据追踪 + 项目本体瘦身（结论）
- 12 个本轮新产物全部 git-tracked；0 外溢 E 盘 / 桌面 / 跨项目。
- 运行数据全锁在 gitignored `.project-local/runs/`（gate-venv / taskpack 解包 / CI 日志 / 临时目录）。
- tracked 1213 文件 **零**误提交构建/缓存；Rust `target/`（2375 文件）、`__pycache__/.pyc`（7518
  文件≈116MB）、`.tsbuildinfo`（260 文件≈15MB）均为 untracked + gitignored 可再生品，
  按规则保留可再生恢复点，不擅自删；5 个 lockfile 为有意 tracked 的注册工具链（NF-11）。

## F. 下一步（用户侧选项）
1. 批准 4 可选卡（付费模型 + 单批授权）→ 升级交付定性至 `ONE_CLIENT_MANAGED` 候选。
2. 授权 NF-07 具体 client/profile/field → 完成实字段受控闭环。
3. 提供 xlsx 工作簿实体 + Excel/WPS 环境 → 完成 WL-R07 工作簿后半程。
4. 安排 Hermes 升级窗口（退出后官方入口）+ hook 交互重批。
5. 如需清理可再生缓存（≈131MB target + pycache + tsbuildinfo），单独授权后执行。

## G. 双端一致性
- 提交链：`693471c → … → acedf3e`（本轮 11 个 commit）；本地 == 远端精确 SHA；worktree clean。
- `work-lab-gate` 全链 success；门禁 10 条命令本地 gate-venv 复验通过。

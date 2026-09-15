# WORK-LAB 集成任务包 20260916 — 收口回执（HEAD 9aace50）

- 交付定性：**READ_ONLY_PREVIEW**（全程零真实全局写 / 零付费调用 / 零凭据 / 零 E 盘 / 零跨项目写）。
- 双端：`r4-recovery-exec` 本地 == 远端 == `9aace50`；`work-lab-gate` 提交链 9aace50 / 51d951f / 659ba93 全 success。
- 回归：`tests/workflow-assistance` 1259 passed / 8 skipped / 0 failed；8 skipped 全为既有 Windows 平台门控
  （symlink 权限 WinError 1314 / POSIX 语义），非本轮引入。

## 1. 16 张必做卡闭环（本轮全部推进）
| 卡 | 交付 | commit |
|---|---|---|
| NF-00 | 基线 693471c 一致 + 基线回执 | 0432b2d |
| NF-01 | 全局执行标准：去死路径/去 force/语义对齐 AGENTS | 0432b2d |
| NF-02 | CI 根因修复：`from services` 硬导入→文件路径加载（gate-safe） | 0432b2d |
| NF-03 | 外溢数据追踪回执（全部锁定 .project-local/runs，gitignored） | 49774f5 |
| NF-04 | 配置事务加固：NOOP / APPLY_FAILED(UNDETERMINED) / COMMITTED_SIMULATED + 4 契约测试 | efbde9e |
| NF-05/06 | 只读客户端价值闭环（脱敏回执）+ 身份/路由 4 契约锁定 | 3a38d48 |
| NF-07 | 单字段受控 apply→readback→恢复（并发保留、幂等、诚实标注未真实适配） | 37f93f6 |
| NF-08 | 最小跨软件 handoff（脱敏载荷 + 差集 4 场景：应答丢失/重启重复/取消后产出/外部未知）+ 承接既有 8 场景 | a3c5061 |
| NF-09 | Observer 投影五态分类（LIVE/ACTUAL_ZERO/STALE/UNKNOWN/UNAUTHORIZED）+ 只读 surface 锁死；前端 80/80 + Python 36/36 回归 | 659ba93 |
| NF-10/11/12 | 收敛审计（技能按需 + 用户原生字段保护 + 依赖清单 + 模型版本差分；无真实调用=UNVERIFIED） | 51d951f |
| WL-R01 | Radar 离线复用闭环（重放不造重复候选 / 版本差分可解释 / 证据不足非高置信 / 中文候选报告 / 不自动晋级） | 9aace50 |
| WL-R07 | 价格身份规范化 + UNKNOWN 传播（缺项→UNKNOWN 不塌缩为 0；套餐/订阅/API/真实消耗分道；旧值保留有效时间；工作簿实体未取得=不杜撰） | 9aace50 |

## 2. 4 张可选卡（包协议默认不执行，需付费模型 + 单批授权）
NF-13、W05、W06、W08 在 `optional_ids`，START-HERMES 明确"默认不执行"；
本轮零真实全局写 → 无 `ONE_CLIENT_MANAGED`。列为用户侧 next-step，不升级为 release blocker。

## 3. 自检 / 审计 / 更新
- 全量回归 1259 绿；双端精确 SHA 一致；CI 提交链全绿（已更新到 HEAD 9aace50）。
- 已修复：NF-02 硬导入、NF-04 状态机、NF-07 受控恢复、NF-09 五态分类、WL-R07 价格身份。

## 4. 项目外溢数据追踪
- 12 个本轮新产物全部 git-tracked（正确交付物），0 外溢 E 盘 / 桌面 / 跨项目。
- 运行数据（gate-venv / taskpack 解包 / CI 日志 / 临时目录）全部锁定 `.project-local/runs/`（gitignored）。
- `CURRENT_STATE` 仅时间戳 churn，已 `git checkout` 恢复到干净提交版。

## 5. 项目本体瘦身
- git-tracked 1213 文件 **零** 误提交的构建/缓存产物。
- Rust `target/`（2375 文件）、`__pycache__`/`.pyc`（7518 文件≈116MB）、`.tsbuildinfo`（260 文件≈15MB）
  全部 **untracked + gitignored 可再生**，按用户规则保留可再生恢复点，不擅自删。
- 5 个 lockfile 为有意 tracked 的注册工具链（NF-11），非污染。

## 6. 停止条件 / 诚实口径
- 16 张必做卡已闭环；4 张可选卡 deferred/需授权；交付定性 READ_ONLY_PREVIEW。
- 不概括为"全任务完成"——可选卡与真实客户端受控写（NF-07 实字段）仍需后续单批授权。

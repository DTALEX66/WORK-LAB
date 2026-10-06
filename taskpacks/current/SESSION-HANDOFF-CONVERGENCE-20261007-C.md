# SESSION HANDOFF — CONVERGENCE 2026-10-07 C

> 上一手：`SESSION-HANDOFF-CONVERGENCE-20261006-B.md`。本文件覆盖 2026-10-07 这一轮的结果与下一步。
> 读序仍按 `AGENTS.md` 的强制链：origin/main 精确提交 → `WORK-LAB-AUTHORITY.md` →
> `.project/governance/project-authority-index.json` → `AGENTS.md` →
> `taskpacks-authority-index.json` → 本登记 → 范围内机器合同 → 本文件。

## 本轮改了什么（结构级别）

1. **`apps/observer/web` 已退役删除**（提交 `891c871`，CI 两条工作流全绿）。
   生产 UI 只有 `apps/observer/frontend`（Vite `dist`，Tauri 打包，sidecar `--frontend-root` 只读服务同一份 dist）。
   审计清单与恢复点：`docs/audits/OBSERVER_WEB_RETIREMENT_MANIFEST_2026-10-07.json`
   （逐文件 SHA-256；`git checkout 6de25fe -- apps/observer/web apps/observer/tests` 可整体还原；
   另有 `.project-local/artifacts/observer-web-retired-20261007/` 副本）。
   **权威文档 §7 已改**，架构文档加了 2026-10-07 规范修订。
2. **旧树 72 条断言全部有归属**：`apps/observer/parity-matrix-u03.md` 是逐条判定表
   （投影 13／只读 24／渲染 19／响应式 11／视觉 5；注意只读面是 17 `t(` ＋ 7 `asyncTest(`）。
   生产侧新账：vitest **17 文件 / 115 条**＋ node 静态契约 **23 条**＋桌面契约 11 条
   ＋ sidecar 浏览器入口 8 条。
3. **修掉 6 类生产真缺陷**（台账 ERR-119…ERR-124）：损坏/不可解析日期被渲染成"可信时刻"或
   "Invalid Date"；缺嵌套对象直接抛；未观测 dirtyCount 显示"干净"；读失败后继续宣称 LIVE；
   载荷不校验／revision 乱序覆盖／`?api=` 不设信任门／缓存可读成当前值；
   窄屏整个应用列被压成 210px（网格轨道）；无数据源时绿色"无告警信号"。
4. **UI 商业级走查有了量具**：`.project-local/runs/convergence-20261007-c/cdp_layout_probe.mjs`
   （零依赖 CDP，Node 22 全局 WebSocket）在指定视口下量真实盒模型；
   `ui_render_shots.py` 做 26 张无窗口截图 + 哈希去重判定。
   证据：`docs/audits/OBSERVER_UI_RENDER_AUDIT_2026-10-07.md`、
   `.project-local/artifacts/ui-audit-20261007/`。

## 下一轮该做什么（按价值排序，都能静默完成）

1. **U02 收尾**：`.gitignore` 遗留条目 + `hermes-project-data.py` 的 `.hermes/` 回退分支
   （行为变更，需先看测试面）；把已修正的受管技能经 `sync_hermes_workflow_assets.py --apply`
   发布到 Hermes Home —— 这是**全局状态**，本轮故意没做。
2. **绿色化（manifest-first）**：候选 `runs/p0c-oracle-20261006` 154 MB、`runs/topbar-measure-20261006` 147 MB、
   `runs/dsh-reconfig-20260904` 134 MB、`runs/ui-suite` 71 MB。
   **绝不碰**：`runs/u19-msvc-20261006/target`（owner 目测产物 + v1 凭据）、导入的 workbuddy 425 MB 唯一副本、
   `toolchains/wl-py311`、DSH 回滚件、gdv 救援补丁、`knowledge-staging`（已证内容不同，不得删）。
3. **UI 剩余项**：品牌 SVG 挂载到头部（已迁入 `frontend/src/assets/brand/`，未挂）；
   `theme/tokens.ts` 声明 `constraints`（矩阵工作单 14）；紧凑面密集项目列表的取舍（15）；
   把 CDP 探针接成 CI 门（目前它只量不门）。
4. **发布链**：release 二进制重建 + 精确 SHA 读回（属 U19/发布工单，非 U08）。

## 本轮踩过的坑（别重复）

- `--dump-dom --virtual-time-budget` 对本应用**必挂**（页面持 SSE 长连接，虚拟时间等不到 idle）；
  `--screenshot` 单用正常。
- in-app 浏览器 MCP 面板是 **0×0 隐藏视口**：能读 DOM 与计算样式，**不能**量布局，也不能截图
  （`NATIVE_BROWSER_VIEWPORT_UNAVAILABLE`）。
- Git Bash 里 `python`/`node` 不在 PATH；sidecar 直跑要 `PYTHONPATH` 用 **`;`** 分隔（Windows 形式）。
- 往 CRLF 工作树用 heredoc 追加会造出混合换行，会让自己的证伪针失效；写完归一化。
- 台账校验器要求 `repeat_prevention` 含祈使词（must/require/never/每/必须），写成陈述句会被拦。
- 断言"某类声明只能出现一次"是错的写法，正确写法是"每一条都必须处在某个门内"。
- 扫描针必须写成"违规的形状"，且**扫不到任何东西时要判失败**（DOM `textContent` 会把标签与数值连成
  `CPU11`，词边界针会静默失明）。

## 静默验证基线（提交前必跑，全绿才算）

```bash
bash .project-local/runs/convergence-20261007-c/run-gate-battery.sh   # BATTERY_FAILURES=0
cd apps/observer && node tests/run_all_tests.js                       # 34 passed
cd apps/observer/frontend && node node_modules/vitest/vitest.mjs run  # 115 passed
node_modules/typescript/bin/tsc -p tsconfig.json --noEmit             # 0
node_modules/vite/bin/vite.js build                                   # 0
python scripts/ci/verify_error_ledger.py                              # PASS entries=123
python scripts/ci/record_blueprint_audit_snapshot.py                  # checks=8 failing=0（需 PATH 带 node/python）
```

证伪脚本（改门禁时必须重跑并全 FALSIFIED）：`falsify_u03_ports.py`(11)、
`falsify_render_ports.py`(8)、`falsify_transport_ports.py`(11)、`falsify_step3_node.py`(4)、
`falsify_step4_node.py`(5)、`falsify_ui_round4.py`(3)。

## 当前状态

分支 `task-decomposition/atlas-gap-archive-20261001`，PR **#162 OPEN**（未合并——合并是 Owner 的动作）。
HEAD `7fc2cc7`；`891c871`（退役）CI 全绿。工作树按内容干净
（仅 `apps/observer/src-tauri/Cargo.toml` 的 CRLF 噪声 `M`，`git diff` 为空）。
未发布：无 tag、无 release（按 owner 指令）。

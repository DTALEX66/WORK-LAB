<!-- freshness: sourceCommit=0da75536f9e0c329fd4881af33b5fa2c091fdcc4 sourceTree=36947bdf1b0e110bd301224d37927fedea6e82e5 generatedAt=2026-08-20T23:59:00Z evidenceLevel=E0 expiry=2026-08-27T16:19:43Z status=STALE -->
# 软件兼容矩阵（SOFTWARE_COMPATIBILITY_MATRIX · 2026-08-19）

| 软件 | 类别 | 官方源 | Adapter | 兼容状态 | 管理方式 |
|---|---|---|---|---|---|
| Hermes | agent-harness | desktop-shortcut | hermes | registered | official baseline + user overlay |
| Codex | agent-runtime | cli | codex | registered | wrapper + rules overlay |
| DeepSeek Harness | agent-runtime | isolated-checkout | deepseek-harness | registered | replaceable (external, D:\\All projects\\DSH) |
| CC Switch | provider-switch | desktop-shortcut | — | registered | registration only |
| Open Design | design-client | desktop-shortcut | open-design | registered | client adapter (design domain owned by DESIGN-LAB) |
| OpenHuman | agent-harness | desktop-shortcut | — | registered | registration only |
| GitHub | platform | api | github | registered | delivery platform |

## 原则

- 全部为注册数据（software-registry.json），不进入核心产品身份
- 配置基线变更需 Diff/Approval/Apply/Readback/Drift/Rollback（config_control_plane.py）
- 版本更新不自动提升 Compatibility Baseline
# WORK-LAB 蓝图同步审计快照

由 `python scripts/ci/record_blueprint_audit_snapshot.py --write` 生成；所有标识、远端 SHA、摘要与退出码均为运行时观察值，不转录自旧报告。本文件不含自身摘要。

## 现场身份

```json
{
  "observedAt": "2026-10-06T22:48:51+0800",
  "remote": "git@github.com:DTALEX66/WORK-LAB.git",
  "branch": "task-decomposition/atlas-gap-archive-20261001",
  "localHead": "a018fbefe4b6f9b67028b5dd12ddbf0eb2a746ed",
  "baseSha": "cd4daa83e107afab8438c0e85f63a10e75314d5a",
  "dirtyFiles": [
    ".project/governance/generated/CURRENT_STATE.json",
    ".project/governance/generated/CURRENT_STATE.md",
    "docs/audits/BLUEPRINT_SYNC_AUDIT_2026-10-06.md",
    "scripts/ci/record_blueprint_audit_snapshot.py",
    "taskpacks/current/error-ledger.json",
    "tests/ci/test_failfast_group.py"
  ],
  "statusRecords": 7,
  "liveMainSha": "cd4daa83e107afab8438c0e85f63a10e75314d5a",
  "liveBranchSha": "a018fbefe4b6f9b67028b5dd12ddbf0eb2a746ed"
}
```

脏文件计数按 `git diff --name-only` 计算：git 状态列会把行尾过滤器改写报成modified，而 `git diff` 无内容差异，因此以 diff 为准（ERR-105 的同一机制）。`liveBranchSha` 为 `NOT-PUSHED` 时表示交付分支尚未同步到远端，不能声称双端完成。

## PR #162 读回

```json
{
  "baseRefName": "main",
  "headRefOid": "a018fbefe4b6f9b67028b5dd12ddbf0eb2a746ed",
  "mergeable": "MERGEABLE",
  "state": "OPEN",
  "url": "https://github.com/DTALEX66/WORK-LAB/pull/162"
}
```

更正记录：蓝图原文记载 PR #162 head 为 `6f323a318a9db1c3a3ed4429bab0d4eff129876c`；本次实时读回是其自身的观察值，两者不同则以上方读回为准，原文值保留为历史观察，不改写。原文记载的 `origin/main = cd4daa83…` 与本次读回一致。

## GitHub About（Git 外元数据）

```json
{
  "before": "Client-neutral AI-agent control plane: user global config overlay for Hermes/Codex/DSH/GitHub/Open Design/OpenHuman via one adapter contract (CC Switch observe-only). Modules: client-neutral-core (task/telemetry ledger, sidecar), services (orchestration/policy/receipts), read-only observer. Authority chain + exact-SHA CI gates.",
  "target": "Client-neutral workflow governance, control and delivery: portable rules, native client adapters, task coordination, permissions and evidence-based completion. Ongoing.",
  "readBackNow": "Client-neutral workflow governance, control and delivery: portable rules, native client adapters, task coordination, permissions and evidence-based completion. Ongoing.",
  "matchesTarget": true,
  "homepageUrl": "(empty — no site claimed)",
  "topicsChanged": false
}
```

About 不属于仓库内容，提交 README 不等于改过 About；此处单独记录 before → target → 现场读回。homepageUrl 与 topics 未改动（无真实站点依据，不编造）。

## exact-SHA CI（PR #162 checks，绑定推送后的 head）

```json
{
  "headSha": "a018fbefe4b6f9b67028b5dd12ddbf0eb2a746ed",
  "count": 22,
  "buckets": {
    "fail": 2,
    "pass": 18,
    "pending": 2
  },
  "pendingOrFailing": [
    {
      "name": "integration",
      "bucket": "fail"
    },
    {
      "name": "observer",
      "bucket": "pending"
    },
    {
      "name": "observer",
      "bucket": "pending"
    },
    {
      "name": "integration",
      "bucket": "fail"
    }
  ]
}
```

本地通过不称为 CI 绿；CI 绿也不宣告产品发布或本机 full gate 通过。

## 输入与摘要

```json
{
  "blueprintDocx": {
    "path": "D:\\All projects\\Record\\02_WORK-LAB_完整项目描述与未来蓝图_20261006.docx",
    "exists": true,
    "sha256": "f3784a9950adce06e8d87015a0ecb39d1ed4fdb3b93d5ccd3c9b40398bea3440",
    "declaredInPrompt": "f3784a9950adce06e8d87015a0ecb39d1ed4fdb3b93d5ccd3c9b40398bea3440",
    "match": true
  },
  "executionPrompt": {
    "path": "D:\\All projects\\Record\\02_WORK-LAB_权威修复_双端描述同步_可审计执行提示词_20261006.txt",
    "exists": true,
    "sha256": "8d4a48185357aeadb99d9a2760a9ba05e6ab4fc744c0e3cb48a12904cf565247",
    "declaredInPrompt": null
  }
}
```

## 检查命令与退出码（本次运行）

| 命令 | 退出码 | 末行结果 |
|---|---|---|
| `scripts/ci/verify_project_authority_reference.py` | 0 | AUTHORITY_REFERENCE_PASS top=WORK-LAB-AUTHORITY.md current=WORK-LAB-UNIFIED-PRODUCT-CONVERGENCE-TASKPACK-20260918 register=OPEN-TASK-REGISTER.md |
| `scripts/ci/verify_error_ledger.py` | 0 | ERROR_LEDGER_PASS entries=108 classifications=13 raw_sensitive_data=false counts_consistent=true |
| `scripts/ci/verify_blueprint_coverage.py` | 0 | BLUEPRINT_COVERAGE_PASS rows=87 kinds={'chapter': 19, 'appendix': 1, 'closed-loop-task': 9, 'owner-default': 5, 'input-source': 11, 'atlas-gap': 20, 'register-row': 22} status_vocabulary=reused dispositions=owner_prompt_ |
| `scripts/ci/failfast_group.py --group observer-web-contracts` | 0 | FAILFAST_GROUP_PASS group=observer-web-contracts commands=10 all_exit_0 |
| `scripts/ci/failfast_group.py --group observer-python-skeleton` | 0 | OK |

## 产物摘要

| 路径 | 字节 | SHA-256 |
|---|---|---|
| `docs/future/WORK-LAB-BLUEPRINT-20261006.md` | 18359 | `4cead2bf8c296b65966a2ad74d8ccdae7dd54ea819dd5aafbfe69b3bee134a73` |
| `docs/future/WORK-LAB-BLUEPRINT-COVERAGE.md` | 34095 | `710e58f5b1cf9c397b15e1662f9e8b99737a6bb2a6c97c1e7a4cd16bb29ad53a` |
| `.project/governance/blueprint-coverage.json` | 25829 | `947b00c088eedcd0ed26359b3f29d14dbabdebec55c31b5d9fd786c124f0a6f5` |
| `scripts/ci/verify_blueprint_coverage.py` | 13822 | `9ded1cd312df28866bd0f5915cf8e1efde120b7725b70463822bbfb2a34ee8f4` |
| `apps/observer/scripts/write_artifact_receipt.py` | 4233 | `83527e3dcef1888e4cc0ce93796cfbd2814ef4e54e7dc367229d3e1fd309b344` |

## 范围与未决缺口

- U19 / T03: the composited desktop surface has not been observed. GDI capture cannot see a WebView2 DirectComposition visual (ERR-104, retracted), and the WebView2 remote-debugging port proved unreliable — it accepts TCP and answers in two early short-timeout attempts but never under patient polling (ERR-107).
- T02: the 2026-10-05 local full gate FAIL (1903 tests, 9 skipped, 12 errors, 22 failures) was never re-run after the runtime fix. Recorded here alongside the affected-group passes below; a group pass is not the aggregate.
- ERR-103: the caption-control ACL grants are proven present in the compiled capability artifact of this build, but the click behaviour has not been re-observed on a desktop (the owner asked for no further window launches).
- ERR-106: the frameless top-row clearance is measured in headless Chrome at a 1262x668 CSS viewport, not in the real 1280x820 logical window.
- AG-19 / T07: the original WORK-LAB long conversation, WORK-LAB-SUMMARY and the 2026-09-28 startup/final attachments remain inaccessible (SOURCE_MISSING).
- Source-side gaps carried honestly: the blueprint has no AG-14 row, merges AG-16/AG-17, omits AG-01..AG-08 and W09, cites OD03/OD04 jointly, and its 19-row candidate pool exceeds the 14-entry registry.
- Merge to main, release, install, global configuration and other-project writes are outside this task's authorization and were not performed.

## 双端同步状态定义

- 本地文件与提交：本报告生成后即成立（读回见上）。
- 远端分支：需推送后以 `git ls-remote` 读回，未读回前一律记 `未验证`。
- GitHub About：Git 外元数据，单独记录 before→after 与读回，不能以提交 README 代替。
- exact-SHA CI：以推送后 PR 的检查读回为准；本地通过不称为 CI 绿。
- 默认分支 main：本轮不合并，故记为未更新。


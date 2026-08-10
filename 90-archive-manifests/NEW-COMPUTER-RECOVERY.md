# 新电脑恢复指南

## 云端真源

```bash
git clone git@github.com:DTALEX66/WORK-LAB.git WORK-LAB
cd WORK-LAB
git checkout main
git rev-parse HEAD
```

当前 `main` 包含三个模块的保留历史、实体工作树、根治理、契约、CI 和交接文档：

- `10-workflow/workflow-assistance`


```bash
```

## 下载迁移执行包

从 GitHub Release `migration-handoff-20260805T091816Z-v4` 下载：

```bash
gh release download migration-handoff-20260805T091816Z-v4 \
  --repo DTALEX66/WORK-LAB \
  --pattern 'work-lab-migration-handoff-20260805T091816Z-v4.zip'
```

解压后保留以下内容：

- `task-pack/`：完整 WORK-LAB v6.0 任务包；
- `evidence/`：DISC/MIG/GOV 交接证据；
- `recovery/`：bundle 清单、SHA-256 和恢复说明。


## 新机验证

```bash
git status --short --branch
git fsck --full
python scripts/security/check_paths.py .
python tests/ci/test_governance_gate.py
python tests/contracts/test_contract_shapes.py
python scripts/ci/aggregate_gate.py <<'JSON'
JSON
```

## 边界

不要把旧仓 dirty patch 自动应用到活动根；先阅读 `working-state/` manifest，再按任务卡逐文件审查。不要删除原机器 archive。旧电脑的 `D:\All projects\WORK-LAB` 尚未被自动切换或清理。

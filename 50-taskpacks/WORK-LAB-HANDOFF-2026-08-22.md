# WORK-LAB 交接总结（2026-08-22）

> 覆盖 08-21 至 08-22 凌晨：WLR 前向收敛全量推进 + Hermes 升级 + skills 吸收 + 模型路由。

## 1. WLR 前向收敛（全量推进）

- R0：基线/supersession 索引/报告新鲜度/错误台账 lifecycle（ee85d2c）
- R1：Observer 严格只读 P0 全闭环（100-160：Tauri 删 Worker 控制/observer_store 只读/token typed/truth-first/动态 endpoint/SSE 游标）（f0776c1）
- P0 硬门：WLR-330 配置真事务（backup/apply/readback/commit-or-rollback + receipt）（670a1d9）
- WLR-410 模型路由引擎：model_router.py（隐私→D/视觉→C/复杂→B/日常→A + RouteLLM 预算降级，零模型调用）（15cae24）
- 批量：260 never-scan / 430 成本真值 / 810 前端单一化 / 910 对抗测试 / 600/640/710/720/820-840 / 920/950（canary 配置 + 批准包）
- CI 修复：test 相对路径（ImportError）+ observer SSE mock（querySelector）（ecf3ac9 / 7859764）
- 测试：workflow 983 passed + observer JS 24/24

## 2. Hermes 0.20.5（08-21）

- 升级 0.20.4→0.20.5（v2026.8.19 tag，uv sync 非 pip）
- remote 修正 SSH；managed overlay 全保留（display.language=zh/memory/hooks/mcp）
- optional-skills/MCP 评估：不启用（169 已够，符合 lean 基线）

## 3. Skills 合并 + 吸收归档

- Hermes 侧 9 个重复 skills 并入 5 主（sqlite/desktop/durable/dsh/CI 组，无丢失）
- 全部工作流软件 skills 吸收到 40-knowledge/asset-provenance/skills/（hermes 171 + codex 17 + dsh 4 = 192，标准化 frontmatter + 索引）

## 4. 模型路由调研（WLR-400/410）

- 行业：Nvidia NeMo Switchyard（降74%）/ Snowflake Cortex / LiteLLM / OpenRouter / RouteLLM（降30-85%）
- WORK-LAB 差异化：规则路由零模型调用 + 客户端中立（借鉴不照搬）
- 报告：reports/current/MODEL_ROUTING_RESEARCH.md

## 5. 会话历史归档（08-20 晚）

- 90-archive/session-history/：HERMES+CODEX+DSH 时间线（229 节点）+ 去重文档（49）

## 6. 运行态

- durable_worker 运行中（Workflow-owned，tick 30，唯一 writer）
- 观测栈守护运行（掉线自动拉起）
- 三仓库双端一致

## 7. 剩余（如实）

- CI 云端转绿确认（已修全部已知失败点，等待 run 完成）
- E5/E6 长期 soak 观察（worker 已启动，数据更新待观察）
- 知识迁移 DEFERRED_BY_USER（40-knowledge 已建，待填充）

## 8. 清理（本轮）

- 临时脚本（build/diagnose/extract/vision 等）已删
- __pycache__ / .pytest_cache 已清
- 工作树干净
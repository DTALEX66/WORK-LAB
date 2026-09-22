- E5/E6 长期 soak 观察（worker 已启动，数据更新待观察）
- 知识迁移 DEFERRED_BY_USER（40-knowledge 已建，待填充）

## 8. 清理（本轮）

- 临时脚本（build/diagnose/extract/vision 等）已删
- __pycache__ / .pytest_cache 已清
- 工作树干净
## 9. 软件更新官方优先规则（2026-08-23 用户硬规则）

- 任何软件更新以官方发布为准（官方 tag/release/安装包），禁止私自本地打包构建版本
- Hermes 官方标准：checkout 官方 tag（v2026.8.19 = 0.20.5）+ uv sync 官方依赖
- 桌面 exe 用官方更新机制/官方安装包获取，不本地 npm run pack
- 2026-08-23 纠正：源码从 main 开发线切回官方 v2026.8.19（fcbd1076a）
- 注意：Hermes.exe（release\win-unpacked）仍是之前本地打包残留（main 版），需用官方更新机制/官方安装包恢复为官方构建（不做本地重打包）
- 基线①已同步（唯一入口 = 官方标准格式）
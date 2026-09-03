# WORK-LAB → Hermes 交接更新（2026-08-21 · 0.20.5 升级）

> 增量：Hermes 0.20.4 → 0.20.5（v2026.8.19）。执行者 DSH。

## 任务 1：Hermes 本体升级 0.20.4 → 0.20.5（完成）

- remote 修正：origin → git@github.com:DTALEX66/hermes-agent.git（SSH，替代 HTTPS 443）；fork/upstream 已 SSH 干净（双引号问题不存在）
- fetch upstream → v2026.8.19 tag → checkout（HEAD fcbd1076a9 'release v0.20.5'）
- uv sync --frozen：0.20.4 → 0.20.5（依赖更新，非 pip——PyPI 仍 0.19.0）
- 验证：hermes-agent version = 0.20.5 ✅
- 用户工作树修改已 stash（pre-0.20.5-upgrade-2026-08-21 等 3 个 stash，可恢复）

## 任务 2：optional-skills + MCP 评估（完成 · 未启用）

- optional-skills 21 类：推荐中文 Windows 开发双轨——software-development / web-development / devops / security / productivity / communication / mlops / data-science / research / mcp
- optional-mcps 19 个：推荐——figma（设计协作）/ comfy-cloud（生成）/ notion / linear / atlassian / asana（项目管理）/ vercel / netlify / supabase / webflow（部署）/ sentry / datadog（监控）/ hugging_face（AI）
- 未启用（启用需用户决定 + 权限审查）

## 任务 3：managed overlay 核对（完成）

- display.language=zh ✅ / memory.*（enabled/user_profile/write_approval/char_limit）✅ / hooks.pre_tool_call ✅ / mcp_servers=context7 ✅
- preserve_unknown 生效——升级后全部保留
- config 自检 OK（load_config 通过）

## 待办

- optional-skills/MCP 启用（等用户选择）
- 旧 stash 清理（升级确认稳定后可丢弃 machine-email-files）
# Runtime Map — 找异常：异常电梯控制台

本文件记录当前游戏目录与现有代码的映射关系。当前阶段只建立分类和 manifest，不搬动运行时代码。

## 入口

| 目标 | 入口 |
|---|---|
| H5 预览 | `index.html` → `src/game.js` |
| 微信小游戏 | `build.js wechat` → `wechat-minigame/game.js` |
| 抖音小游戏 | `build.js douyin` → `douyin-minigame/game.js` |
| Android WebView | `scripts/prepare-android-webview.mjs` → `android-webview/app/src/main/assets/` |

## 核心模块

| 模块 | 路径 |
|---|---|
| 状态机 | `src/state.js` |
| 玩家动作 | `src/actions.js` |
| 异常事件 | `src/events.js` |
| 反馈/失败总结 | `src/feedback.js` |
| 运行时调度 | `src/runtimeSession.js` |
| 皮肤管理 | `src/skinManager.js` |
| 皮肤文案/UI 标签 | `src/uiLabels.js` |
| 档案库 | `src/archive.js` |
| 埋点 | `src/analytics.js` |

## 不移动源码的原因

当前 H5、微信、Android WebView 和测试脚本都依赖根部路径。为了保持本次改动可回滚，本轮只完成平台定位和目录索引；后续源码迁移需单独执行并配套修改 build/test。

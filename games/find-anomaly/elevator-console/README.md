# 找异常：异常电梯控制台

## 所属平台分类

```text
MINIGAME / games / find-anomaly / elevator-console
```

## 游戏定位

这是 MINIGAME 小游戏合集平台中的首发游戏，玩法归类为 **找异常**。

玩家不是单纯模拟电梯操作员，而是在 CCTV、状态 HUD 和系统日志中寻找异常，并在倒计时内完成处置。

## 当前运行时映射

当前实现仍复用仓库根部运行时：

| 功能 | 当前路径 |
|---|---|
| H5 入口 | `index.html`, `styles.css`, `src/game.js` |
| 核心逻辑 | `src/state.js`, `src/actions.js`, `src/events.js`, `src/feedback.js` |
| 内容包/皮肤 | `src/skins/*/skin.json` |
| Canvas 小游戏 runtime | `platform/miniGameRuntime.js`, `platform/canvasRenderer.js` |
| 微信产物 | `wechat-minigame/` |
| Android WebView | `android-webview/` |

## 当前内容包

首发游戏已包含 5 套场景皮肤：

- `elevator`：异常电梯控制台
- `security`：安防监控室
- `factory`：工厂夜班控制室
- `subway`：地铁末班调度室
- `hospital`：深夜医院值班台

## 后续扩展

优先扩展：

1. `hotel`：无人酒店前台 / 午夜入住异常
2. 皮肤选择界面
3. 异常档案库图鉴化
4. 找异常分类下的第二个独立游戏

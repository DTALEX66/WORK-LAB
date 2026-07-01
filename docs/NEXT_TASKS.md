# MINIGAME 后续任务列表

> 依据 `docs/PROJECT_CONTEXT.md`、`docs/GAME_DESIGN.md`、当前代码/测试/构建状态整理。
>
> 当前基线：`npm run verify` 通过；`npm test` 当前为 70/70 pass；微信 strict 为 0 blocker；Android APK build/inspect 通过；`npm run release:check` 在默认占位配置下预期失败，当前有 4 个发布 blocker。

## P0｜马上该做：防止交付信息/验证链漂移

### 1. 修正 README 的测试数量硬编码

当前真实测试数会随用例增加变化，README 不应长期硬编码过期数字。

**任务：**

- README 改成“以 `npm run verify` 输出为准”，或新增脚本自动更新/校验测试数量。
- 更新 `tests/docs.test.js`，避免只检查“存在测试数”而不检查一致性。

**验收：**

```bash
npm test
npm run verify
```

### 2. 新增命令清单一致性测试

多个文档都会写构建/验收命令，容易漂移。

**任务：**

- 新增 `tests/docsCommands.test.js`。
- 检查 `README.md`、`android-webview/README.md`、`docs/ANDROID_APK_HANDOFF.md` 是否包含：
  - `npm run verify`
  - `npm run android:build`
  - `npm run android:inspect`
  - `npm run release:check`
  - `release.config.example.json`
- 检查不再出现过期描述：
  - “当前环境缺少 Android 构建工具”
  - “只有文字监控”
  - “需要下拉整页”

**价值：** 防止入口文档再次漂移。

### 3. 给 `npm run verify` 增加简洁摘要模式

当前 `npm run verify` 输出很长，不利于自动循环/CI 快速判断。

**任务：**

支持：

```bash
npm run verify -- --summary
```

或新增：

```bash
npm run verify:summary
```

输出示例：

```text
[verify] tests: pass
[verify] wechat strict: 0 blocker
[verify] android build: OK
[verify] apk metadata: OK
```

## P1｜发布前必须做：真实平台发布链

### 4. 填真实 `release.config.json` 并验证发布检查通过

当前 `npm run release:check` 预期失败，因为没有真实：

- 微信小游戏 AppID
- 复活广告位 `revive`
- 日志解锁广告位 `decode`
- 真相提示广告位 `truth`

**任务：**

```bash
cp release.config.example.json release.config.json
```

填入真实值后运行：

```bash
node build.js wechat
npm run release:check
```

**验收：**

```text
release blocker(s): 0
```

**注意：** 真实 AppID / adUnitId 不提交。

### 5. 微信开发者工具真实导入测试

当前仓库通过 bundle 静态检查证明微信 runtime 不含 DOM/window blocker，但还没有本机微信开发者工具导入实测记录。

**任务：**

- 安装/定位微信开发者工具。
- 用真实 AppID 打开 `wechat-minigame/`。
- 验证：
  - Canvas 能启动。
  - 触摸操作生效。
  - 奖励广告创建流程不报错。
  - `wx.createRewardedVideoAd` 路径可走。

**验收：**

- 记录截图/日志。
- 更新 `docs/WECHAT_REGRESSION_REPORT.md`。

### 6. 真广告失败兜底策略完善

当前广告失败时偏开发友好，适合模拟环境；上线需要区分 dev/release。

**任务：**

- 区分开发模式与发布模式：
  - 开发模式：广告失败也可给奖励，避免阻塞测试。
  - 发布模式：广告失败提示重试/稍后再试，不无条件发奖励。
- 可通过 `release.config.json` 或环境变量控制：

```json
{
  "releaseMode": true
}
```

**验收：**

- 浏览器模拟广告仍可用。
- 微信 release 模式不再无条件发奖励。
- 测试覆盖两种模式。

## P2｜产品留存/变现增强

### 7. 增加局后总结/复盘页

当前已有失败、复活、隐藏日志，但缺少清晰的玩家局后复盘。

**任务：**

游戏结束后展示：

- 存活秒数
- 触发异常数
- 最危险异常
- 解锁隐藏日志数
- 是否触发假结局
- “再试一次”
- “看广告解锁异常档案”

**价值：** 增强循环、增加广告触点、提高重玩动机。

### 8. 增加异常档案库长期收集系统

当前隐藏日志是局内解锁，但缺少跨局收藏目标。

**任务：**

- 新增本地存档：
  - 已见过异常
  - 已解锁隐藏日志
  - 皮肤维度收集进度
- UI 增加“档案库”。
- 广告解锁可推进档案收集。

**价值：** 从单局小游戏变成可留存产品。

### 9. 加入轻量数据埋点接口

即使先不接真实后端，也应有统一事件接口。

**任务：**

新增：

```text
src/analytics.js
```

记录事件：

- `game_start`
- `game_over`
- `revive_ad_start`
- `revive_ad_reward`
- `hidden_log_ad_start`
- `hidden_log_unlock`
- `fake_ending_trigger`
- `action_click`
- `anomaly_trigger`

浏览器先 `console.log`，微信/抖音后续可接平台分析。

## P3｜批量复制/换皮生产系统

### 10. 皮肤 JSON Schema 校验

已有 3 个皮肤，但缺少正式 schema 文件。

**任务：**

新增：

```text
schemas/skin.schema.json
scripts/validate-skins.mjs
npm run skins:check
```

检查：

- `meta` 完整
- `ui` 文案完整
- `actionFeedback` 完整
- 12 个 anomaly
- 12 个 hiddenLog
- 所有 action label 存在
- 不能缺关键字段

**验收：**

```bash
npm run skins:check
npm run verify
```

### 11. 新增皮肤生成模板

目标是批量复制小游戏。

**任务：**

新增：

```text
templates/skin-template.json
docs/SKIN_AUTHORING_GUIDE.md
```

说明如何生成新皮肤：

- 主题
- 异常列表
- 隐藏日志
- 操作文案
- UI 文案
- 假结局文案

### 12. 做第 4 套皮肤作为生产验证

已有：

- 电梯
- 安防
- 工厂

建议第 4 套做更强商业化题材：

1. 深夜医院值班台
2. 地铁末班调度室
3. 无人酒店前台
4. 海上钻井平台控制室
5. 校园广播室异常值班

推荐优先：**地铁末班调度室**。

理由：

- 与电梯一样适合控制台。
- 异常空间强。
- 视觉可复用：车厢、站台、摄像头、信号灯。
- 容易扩展到下一款游戏。

## P4｜平台工程/CI

### 13. GitHub Actions 自动验收

现在本地 `npm run verify` 能跑，但 GitHub 还没有自动验收。

**任务：**

新增：

```text
.github/workflows/verify.yml
```

先跑轻量部分：

```bash
npm test
node build.js wechat
node scripts/check-wechat-bundle.mjs --strict
```

Android APK 构建可分两步：

- 先不放 CI，避免工具链体积问题。
- 后续再缓存 Android SDK。

### 14. Android release APK / 签名流程

当前是 debug APK。

**任务：**

- 增加 release build 文档。
- 增加签名配置模板。
- 私有 keystore 不提交。
- 输出：

```text
app-release.apk
```

### 15. 真机安装自动化脚本

新增：

```text
scripts/install-android-debug.mjs
npm run android:install
```

执行：

```bash
adb devices -l
adb install -r app-debug.apk
adb shell am start -n com.dtalex.minigame/.MainActivity
```

## P5｜体验打磨

### 16. 游戏内新手引导压缩

首局玩家可能还不知道每个按钮的风险。

**任务：**

- 首局前 10 秒高亮推荐操作。
- 第一次异常时显示“应该优先看监控/日志”。
- 第一次失败时解释复活逻辑。

### 17. 监控画面继续拟真化

当前已有 CCTV 视觉层，但还能继续增强：

- 信号雪花噪声
- 画面撕裂
- 红外轮廓闪烁
- 异常发生时短暂 freeze frame
- 不同皮肤不同监控视觉元素

### 18. 音效和震动反馈增强

已有 Web Audio 程序化音效，移动端可继续增加：

- 按钮点击短震
- 异常触发强震
- 失败低频噪声
- 广告复活成功提示音

微信/抖音需要平台能力抽象。

## 建议执行顺序

如果继续自动推进，建议：

1. P0-1：修 README 测试数量硬编码/文档漂移测试。
2. P3-10：新增 skin schema + `npm run skins:check`。
3. P2-7：局后总结/复盘页。
4. P2-8：异常档案库跨局收集。
5. P1-6：广告 release/dev 模式区分。
6. P4-13：GitHub Actions 自动验收。

当前最推荐下一步：**新增 skin schema + `npm run skins:check`**。

理由：项目核心目标是“可复制、可换皮、批量生产”，皮肤 schema 是下一阶段生产系统的地基。

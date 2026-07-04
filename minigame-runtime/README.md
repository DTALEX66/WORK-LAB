# MINIGAME

> 单人 AI 驱动的小游戏生产与变现系统（Indie AI Game Production System）

当前主线不是普通小游戏合集，而是围绕 **异常系统模拟类小游戏** 建立可复制、可换皮、可接入 IAA 广告变现的生产系统。

## 当前原型

**异常电梯控制台**

玩家扮演夜班电梯异常控制员，不是在看剧情，而是在操作一个不断出错的系统：

- 观察楼层、电梯门、电源、稳定度、异常等级、乘客数量
- 在一屏控制台里执行开门、关门、上行、下行、急停、系统重启、查看日志
- 处理随机异常事件和逐步升高的系统压力
- 通过失败复活、隐藏日志解锁、假结局真相提示形成 IAA 广告循环
- 在监控面板中看到 CCTV/电梯轿厢/乘客热源/异常准星，不再只是文字提示

## 当前能力快照

- H5/Android WebView：`100dvh` 竖屏一屏布局，页面级滚动关闭，面板内滚动
- 微信/抖音小游戏：独立 Canvas runtime，严格检查已确保不依赖 DOM/window
- 换皮系统：皮肤 JSON 驱动，已包含电梯、安防、工厂、地铁、医院 5 套皮肤
- Android APK：项目内便携 JDK/Gradle/Android SDK 工具链已验证可构建 debug APK
- 发布安全：真实 AppID / adUnitId 走 ignored 私有配置，不提交源码
- 数据基础：轻量 `src/analytics.js` 埋点接口已接入 H5 游戏关键路径
- 留存基础：跨局异常档案库已按皮肤记录遭遇异常、解锁日志和收集进度
- 视觉资产：`docs/IMAGE_GENERATION_PROMPT_PACK.md` 收录真实 CCTV / 控制台 / HUD 材质生成词汇

## 快速开始

```bash
npm install
npm run serve
```

然后访问：

```text
http://127.0.0.1:5173
```

## 一键开发验收

```bash
npm run verify
```

该命令会完整执行：

1. `npm test`
2. 微信小游戏构建
3. 微信 strict bundle 检查
4. Android debug APK 构建
5. Android APK 元数据检查

当前已验证：`npm run verify` 通过（测试数以实际输出为准），微信 strict 为 0 blocker，Android APK 可构建。

## Android APK

```bash
npm run android:build
npm run android:inspect
```

产物：

```text
android-webview/app/build/outputs/apk/debug/app-debug.apk
```

详细交接见：

```text
docs/ANDROID_APK_HANDOFF.md
```

## 微信/抖音小游戏构建

```bash
node build.js wechat
node scripts/check-wechat-bundle.mjs --strict
```

微信产物：

```text
wechat-minigame/game.js
wechat-minigame/game.json
wechat-minigame/project.config.json
```

> `project.config.json` 中的公开 AppID 是占位值，真实发布 AppID 不应提交到仓库。

## 发布前私有配置

仓库只提交安全模板：

```bash
cp release.config.example.json release.config.json
```

然后在本地 `release.config.json` 填入真实值：

```json
{
  "wechat": {
    "appid": "真实微信小游戏 AppID",
    "projectname": "MINIGAME"
  },
  "adUnits": {
    "revive": "真实复活广告位",
    "decode": "真实日志解锁广告位",
    "truth": "真实真相提示广告位"
  }
}
```

发布前运行：

```bash
npm run release:check
```

默认占位配置下该命令会故意失败；填入真实私有配置后才应通过。

## 常用命令

```bash
npm run serve            # 本地 H5 预览
npm test                 # Node16 兼容测试入口
npm run verify           # 一键开发验收
npm run android:build    # 构建 Android WebView debug APK
npm run android:inspect  # 检查 APK 包名、应用名、图标、SDK
npm run android:install  # 安装并启动 Android debug APK（需 adb 设备在线）
npm run release:check    # 发布前检查：真实 AppID/adUnitId + runtime blocker
npm run skin:new -- <id> [名称]  # 从模板生成新皮肤
node build.js wechat     # 构建微信小游戏 bundle
```

## 当前文档

- `docs/PROJECT_CONTEXT.md`：项目单一事实源
- `docs/WORKFLOW.md`：AI 协作与开发约束
- `docs/YOLO_BOUNDARIES.md`：YOLO 自主执行边界
- `docs/GAME_DESIGN.md`：异常电梯控制台设计总纲
- `docs/P1_MONETIZATION_LOOP.md`：变现循环设计
- `docs/P2_SKINNING_SYSTEM.md`：换皮系统设计
- `docs/P3_PLATFORM_ADAPTATION.md`：平台适配设计
- `docs/ANDROID_APK_HANDOFF.md`：Android APK 构建/安装/调试交接
- `docs/NEXT_TASKS.md`：后续任务列表与建议执行顺序
- `docs/CONTENT_PACK_SPEC.md`：内容包协议与当前 skin 映射
- `docs/SKIN_AUTHORING_GUIDE.md`：新皮肤生成流程与模板使用说明
- `docs/GAME_BASE_SELECTION.md`：开源小游戏底座评分表

## 开发原则

- 每次只做一个功能
- 先设计，后开发
- 所有修改必须可回滚
- 不偏离“异常系统模拟类小游戏”主线
- 真实 AppID / adUnitId / 私密配置只放 ignored 本地文件，不提交源码

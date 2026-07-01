# Android APK WebView Adaptation

本目录是当前 H5 游戏的 Android WebView 包装工程，用于后续生成 APK，在小米 17 和雷电模拟器中验收。

## 当前策略

- 不替换当前游戏源码。
- 不接入微信 Canvas runtime。
- Android 先走 WebView 包装当前 H5 版本。
- JS 使用 `build.js android` 生成的单文件 IIFE，避免 Android `file://` 下 ES module 加载限制。

## 适配目标

### 小米 17

- 竖屏锁定。
- 全屏沉浸式。
- WebView text zoom 固定为 100%，避免系统字体缩放破坏 HUD。
- 使用 `100dvh` / 移动端 CSS 规则，适配高屏占比。

### 雷电模拟器

- minSdk 23，兼容常见 Android 7+ 模拟器环境。
- 竖屏运行。
- 允许本地 file asset 访问。
- 不依赖外网。

## 准备 WebView assets

在项目根目录运行：

```bash
node scripts/prepare-android-webview.mjs
```

生成：

```text
android-webview/app/src/main/assets/index.html
android-webview/app/src/main/assets/styles.css
android-webview/app/src/main/assets/game.js
```

## 构建 APK

本项目已支持项目内便携 Android 工具链，默认安装在：

```text
D:\All projects\MINIGAME\.tools
```

不需要改系统环境变量。

一键构建：

```bash
npm run android:build
```

等价于：

```bash
node scripts/build-android-debug.mjs
```

也可以在有 Android Studio 或 Android SDK 的机器上：

```bash
cd android-webview
./gradlew assembleDebug
```

或在 Windows Android Studio 中导入：

```text
D:\All projects\MINIGAME\android-webview
```

产物路径通常为：

```text
android-webview/app/build/outputs/apk/debug/app-debug.apk
```

## 验收清单

1. 安装到小米 17 或雷电模拟器。
2. 启动后应全屏竖屏显示“等待接管异常电梯”。
3. 点击“开始接管”。
4. 点击“触发异常测试”。
5. 检查：
   - 监控 HUD 出现 `SIGNAL: UNSTABLE` / `THREAT`。
   - 操作按钮可点击。
   - 日志高亮清晰。
   - 失败弹层可滚动、按钮可点。
   - 没有横向滚动、遮挡或表单感。

## 已知限制

- 当前未集成原生广告 SDK；广告仍为模拟广告。
- 当前 APK 是 WebView 包装，不是微信小游戏 Canvas runtime。
- 当前环境缺少 Android 构建工具，需在装有 Android Studio/SDK 的机器上产出 APK。

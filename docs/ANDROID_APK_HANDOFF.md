# Android APK 包装工程交接

这份说明用于下一台电脑继续在本项目目录内安装、构建、调试 Android WebView APK。

## 当前状态

当前 Android APK 包装走 WebView 方案：

- Android 工程目录：`android-webview/`
- APK 构建命令：`npm run android:build`
- APK 输出：`android-webview/app/build/outputs/apk/debug/app-debug.apk`
- 包名：`com.dtalex.minigame`
- 入口 Activity：`com.dtalex.minigame/.MainActivity`

当前已在雷电/Android 模拟器验证：

- APK 可安装。
- 应用可启动。
- “开始接管”可点击。
- 点击后倒计时从 60 开始下降。
- 操作面板可显示。
- “触发异常测试”可进入游戏内失败弹层。
- logcat 未再出现 `SKIN_DATA is not defined`、`_getHiddenLog`、`RangeError` 等启动错误。

## 下一台电脑从零开始

### 1. 拉代码

```bash
git clone git@github.com:DTALEX66/MINIGAME.git
cd MINIGAME
```

如果已经有本地目录：

```bash
cd MINIGAME
git pull --ff-only origin main
```

### 2. 安装 Node 依赖

```bash
npm install
```

### 3. 准备项目内便携 Android 工具链

本项目不要求改系统环境变量；工具链默认放在项目内：

```text
.tools/
.gradle/
```

如果 `.tools/` 不存在，需要安装：

- JDK 17
- Gradle 8.10.2
- Android SDK commandline-tools
- Android SDK Platform 35
- Android Build Tools 35.0.0
- Android Platform Tools / adb

已验证可用的项目内环境变量：

```bash
export JAVA_HOME="$(pwd)/.tools/java/jdk-17"
export ANDROID_HOME="$(pwd)/.tools/android-sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export GRADLE_USER_HOME="$(pwd)/.gradle"
export PATH="$JAVA_HOME/bin:$(pwd)/.tools/gradle/gradle-8.10.2/bin:$ANDROID_HOME/platform-tools:$PATH"
```

> 注意：`.tools/` 和 `.gradle/` 已在 `.gitignore`，不会上传到仓库。下一台电脑如果没有工具链，需要重新安装或复制 `.tools/`。

### 4. 构建 APK

```bash
npm run android:build
```

成功后产物：

```text
android-webview/app/build/outputs/apk/debug/app-debug.apk
```

### 5. 安装到雷电模拟器或小米手机

先确认设备：

```bash
adb devices -l
```

如果是雷电模拟器，常见连接端口可尝试：

```bash
adb connect 127.0.0.1:5555
adb connect 127.0.0.1:5554
adb connect 127.0.0.1:62001
adb connect 127.0.0.1:7555
adb devices -l
```

安装：

```bash
adb install -r android-webview/app/build/outputs/apk/debug/app-debug.apk
```

启动：

```bash
adb shell am start -n com.dtalex.minigame/.MainActivity
```

如果需要强制重启应用：

```bash
adb shell am force-stop com.dtalex.minigame
adb shell am start -n com.dtalex.minigame/.MainActivity
```

### 6. 调试 logcat

Android WebView 的 JS console 已接入 logcat，tag 是：

```text
MINIGAME_WEBVIEW
```

查看错误：

```bash
adb logcat -d -t 300 | grep -iE 'MINIGAME_WEBVIEW|Uncaught|ReferenceError|TypeError|RangeError|FATAL'
```

清空日志后重测：

```bash
adb logcat -c
adb shell am force-stop com.dtalex.minigame
adb shell am start -n com.dtalex.minigame/.MainActivity
```

### 7. 推荐验收路径

1. 启动 APK。
2. 确认首屏不是黑屏/白屏，显示“等待接管异常电梯”。
3. 点击“开始接管”。
4. 确认倒计时从 60 下降。
5. 点击：
   - 开门
   - 关门
   - 上行
   - 下行
   - 急停
   - 系统重启
   - 查看日志
6. 点击“触发异常测试”。
7. 确认异常/失败弹层是游戏内 UI，不是 Android 崩溃。
8. 点击“观看广告复活”，确认模拟广告路径可用。

## 当前已修过的 APK 启动问题

### 问题 1：开始接管没反应

实际根因不是触摸坐标，而是 Android bundle 初始化失败，导致按钮事件没有绑定。

已修复：

- `build.js` 正确把 `SKIN_DATA` 映射到 `__SKIN_DATA__`。
- `build.js` 正确处理 `getHiddenLog as _getHiddenLog` alias。
- `src/game.js` 增加 `bindPress()`，同时绑定 `click` / `touchend` / `pointerup`。
- `MainActivity.java` 接入 WebView console 到 logcat。

### 问题 2：修复 SKIN_DATA 后出现递归爆栈

错误：

```text
Uncaught RangeError: Maximum call stack size exceeded
```

原因：打包器把兼容 wrapper 替换成递归调用。

已修复：构建时移除该 wrapper，并直接使用 skinManager 的 `getHiddenLog`。

## 常用命令汇总

```bash
npm test
npm run android:build
adb devices -l
adb install -r android-webview/app/build/outputs/apk/debug/app-debug.apk
adb shell am force-stop com.dtalex.minigame
adb shell am start -n com.dtalex.minigame/.MainActivity
adb logcat -d -t 300 | grep -iE 'MINIGAME_WEBVIEW|Uncaught|ReferenceError|TypeError|RangeError|FATAL'
```

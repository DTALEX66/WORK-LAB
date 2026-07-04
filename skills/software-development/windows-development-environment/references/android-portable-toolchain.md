# Portable Android toolchain in a Windows project

Use this when a project wants Android APK builds without changing system-wide environment variables. Keep the toolchain under the project root and ignore it in git.

## Target layout

```text
.tools/
  java/jdk-17/
  gradle/gradle-8.10.2/
  android-sdk/
    cmdline-tools/latest/
    platform-tools/
    platforms/android-35/
    build-tools/35.0.0/
.gradle/
```

Add `.tools/` and `.gradle/` to `.gitignore`; do not commit downloaded SDK/JDK/Gradle files.

## Windows/Git Bash pitfalls

### 1. PATH may point to an old Node

WeChat DevTools can put Node 16 earlier in PATH. Scripts that use `import.meta.dirname` fail on Node 16.

Portable fix in `.mjs` scripts:

```js
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '..');
```

Prefer this over `import.meta.dirname` for project scripts that may run under Node 16.

### 2. `.bat` with paths containing spaces under Git Bash

Directly invoking `sdkmanager.bat` from Git Bash can split paths like `D:\All projects\...` into `D:\All`. A project-local `.cmd` wrapper is safer.

Example wrapper:

```bat
@echo off
setlocal
set "ROOT=D:\All projects\MINIGAME"
set "JAVA_HOME=%ROOT%\.tools\java\jdk-17"
set "ANDROID_HOME=%ROOT%\.tools\android-sdk"
set "ANDROID_SDK_ROOT=%ANDROID_HOME%"
set "GRADLE_USER_HOME=%ROOT%\.gradle"
set "PATH=%JAVA_HOME%\bin;%ROOT%\.tools\gradle\gradle-8.10.2\bin;%ANDROID_HOME%\platform-tools;%PATH%"

call gradle --version
call "%ANDROID_HOME%\cmdline-tools\latest\bin\sdkmanager.bat" --sdk_root="%ANDROID_HOME%" "platform-tools" "platforms;android-35" "build-tools;35.0.0"
endlocal
```

Important: use `call gradle --version` (not bare `gradle --version`) inside `.cmd`, otherwise the parent script can terminate after `gradle.bat` returns.

### 3. Android SDK licenses in project-local SDKs

If `yes | sdkmanager --licenses` does not feed input correctly through `.bat`, license acceptance may still fail. For project-local SDKs, create standard license files under `.tools/android-sdk/licenses/` before installing packages:

```text
android-sdk-license:
24333f8a63b6825ea9c5514f83c2829b004d1fee
8933bad161af4178b1185d1a37fbf41ea5269c55
d56f5187479451eabf01fb78af6dfcb131a6481e

android-sdk-preview-license:
84831b9409646a918e30573bab4c9c91346d8abd
```

Then run `sdkmanager.bat --sdk_root="%ANDROID_HOME%" "platform-tools" "platforms;android-35" "build-tools;35.0.0"`.

## Verification checklist

Run the project’s documented build command, not only a one-off direct Node command:

```bash
npm run android:build
```

Then verify:

```bash
ls -lh android-webview/app/build/outputs/apk/debug/app-debug.apk
sha256sum android-webview/app/build/outputs/apk/debug/app-debug.apk
```

If a generated asset file appears modified but `git diff --stat` shows no actual content change, restore it to avoid committing line-ending churn:

```bash
git checkout -- android-webview/app/src/main/assets/game.js
```

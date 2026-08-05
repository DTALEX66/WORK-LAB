import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '..');
const javaHome = resolve(root, '.tools/java/jdk-17');
const androidHome = resolve(root, '.tools/android-sdk');
const gradleBin = resolve(root, '.tools/gradle/gradle-8.10.2/bin');

for (const [name, path] of Object.entries({ javaHome, androidHome, gradleBin })) {
  if (!existsSync(path)) {
    throw new Error(`${name} missing: ${path}\nRun the portable Android toolchain install first.`);
  }
}

const env = {
  ...process.env,
  JAVA_HOME: javaHome,
  ANDROID_HOME: androidHome,
  ANDROID_SDK_ROOT: androidHome,
  GRADLE_USER_HOME: resolve(root, '.gradle'),
  PATH: [
    resolve(javaHome, 'bin'),
    gradleBin,
    resolve(androidHome, 'platform-tools'),
    process.env.PATH || '',
  ].join(process.platform === 'win32' ? ';' : ':'),
};

execFileSync(process.execPath, ['scripts/prepare-android-webview.mjs'], {
  cwd: root,
  env,
  stdio: 'inherit',
});

const gradleCommand = process.platform === 'win32'
  ? [process.env.COMSPEC || 'cmd.exe', ['/d', '/s', '/c', 'gradle.bat --no-daemon assembleDebug']]
  : ['gradle', ['--no-daemon', 'assembleDebug']];

execFileSync(gradleCommand[0], gradleCommand[1], {
  cwd: resolve(root, 'android-webview'),
  env,
  stdio: 'inherit',
});

console.log('\n[android] APK: android-webview/app/build/outputs/apk/debug/app-debug.apk');

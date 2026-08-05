import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const androidHome = process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT || resolve(root, '.tools/android-sdk');
const adb = resolve(androidHome, 'platform-tools', process.platform === 'win32' ? 'adb.exe' : 'adb');
const apkPath = resolve(root, 'android-webview/app/build/outputs/apk/debug/app-debug.apk');
const packageName = 'com.dtalex.minigame';
const activityName = 'com.dtalex.minigame/.MainActivity';

function androidEnv() {
  return {
    ...process.env,
    ANDROID_HOME: androidHome,
    ANDROID_SDK_ROOT: androidHome,
    PATH: [resolve(androidHome, 'platform-tools'), process.env.PATH || ''].join(process.platform === 'win32' ? ';' : ':'),
  };
}

function run(label, command, args, options = {}) {
  console.log(`[android-install] ${label}: ${command} ${args.join(' ')}`);
  return execFileSync(command, args, {
    cwd: root,
    stdio: 'inherit',
    env: androidEnv(),
    ...options,
  });
}

function getDevices() {
  console.log('[android-install] adb devices -l');
  const output = execFileSync(adb, ['devices', '-l'], {
    cwd: root,
    encoding: 'utf8',
    env: androidEnv(),
  });
  process.stdout.write(output);
  return output.split(/\r?\n/).filter(line => /\bdevice\b/.test(line) && !line.startsWith('List of'));
}

if (!existsSync(adb)) {
  throw new Error(`adb not found: ${adb}\nRun the portable Android toolchain install first, or set ANDROID_HOME.`);
}

if (!existsSync(apkPath)) {
  throw new Error(`APK not found: ${apkPath}\nRun npm run android:build first.`);
}

const devices = getDevices();
if (devices.length === 0) {
  console.error('[android-install] No Android device/emulator is online. Start 雷电模拟器 or enable USB debugging, then rerun npm run android:install.');
  process.exit(1);
}

run('install', adb, ['install', '-r', apkPath]);
run('force-stop', adb, ['shell', 'am', 'force-stop', packageName]);
run('start', adb, ['shell', 'am', 'start', '-n', activityName]);
console.log('[android-install] OK');

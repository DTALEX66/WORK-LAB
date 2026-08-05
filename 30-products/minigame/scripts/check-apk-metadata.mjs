import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const apkPath = resolve(root, 'android-webview/app/build/outputs/apk/debug/app-debug.apk');
const expected = {
  packageName: 'com.dtalex.minigame',
  label: '异常电梯控制台',
  icon: 'ic_launcher',
  sdkVersion: '23',
  targetSdkVersion: '35',
};

function candidateAapts() {
  const sdkRoots = [
    process.env.ANDROID_HOME,
    process.env.ANDROID_SDK_ROOT,
    resolve(root, '.tools/android-sdk'),
  ].filter(Boolean);

  const versions = ['35.0.0', '34.0.0'];
  const candidates = [];
  for (const sdk of sdkRoots) {
    for (const version of versions) {
      candidates.push(join(sdk, 'build-tools', version, process.platform === 'win32' ? 'aapt.exe' : 'aapt'));
    }
  }
  return [...new Set(candidates)];
}

function findAapt() {
  return candidateAapts().find(path => existsSync(path));
}

function requireMatch(text, regex, message) {
  if (!regex.test(text)) {
    console.error(`[apk-check] FAIL: ${message}`);
    process.exitCode = 1;
  } else {
    console.log(`[apk-check] PASS: ${message}`);
  }
}

if (!existsSync(apkPath)) {
  console.error(`[apk-check] APK not found: ${apkPath}`);
  console.error('[apk-check] Run npm run android:build first.');
  process.exit(1);
}

const aapt = findAapt();
if (!aapt) {
  console.error('[apk-check] aapt not found under ANDROID_HOME/ANDROID_SDK_ROOT/.tools/android-sdk');
  process.exit(1);
}

const badging = execFileSync(aapt, ['dump', 'badging', apkPath], { encoding: 'utf8' });
console.log(`[apk-check] aapt: ${aapt}`);
console.log(`[apk-check] apk: ${apkPath}`);

requireMatch(badging, new RegExp(`package: name='${expected.packageName}'`), `package is ${expected.packageName}`);
requireMatch(badging, new RegExp(`application-label:'${expected.label}'`), `label is ${expected.label}`);
requireMatch(badging, new RegExp(`application: label='${expected.label}' icon='[^']*${expected.icon}`), 'launcher icon is branded ic_launcher resource');
requireMatch(badging, new RegExp(`sdkVersion:'${expected.sdkVersion}'`), `min sdk is ${expected.sdkVersion}`);
requireMatch(badging, new RegExp(`targetSdkVersion:'${expected.targetSdkVersion}'`), `target sdk is ${expected.targetSdkVersion}`);

if (process.exitCode) process.exit(process.exitCode);
console.log('[apk-check] OK');

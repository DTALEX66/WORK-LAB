import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const rootReadme = readFileSync(new URL('../README.md', import.meta.url), 'utf8');
const androidReadme = readFileSync(new URL('../android-webview/README.md', import.meta.url), 'utf8');

test('root README documents current verification and release gates', () => {
  assert.match(rootReadme, /npm run verify/, 'README should advertise the one-command development gate');
  assert.match(rootReadme, /68\/68/, 'README should document the current verified test count');
  assert.match(rootReadme, /npm run release:check/, 'README should advertise release readiness check');
  assert.match(rootReadme, /release\.config\.example\.json/, 'README should document private release config template');
  assert.match(rootReadme, /android-webview\/app\/build\/outputs\/apk\/debug\/app-debug\.apk/, 'README should point to APK output');
  assert.match(rootReadme, /CCTV\/电梯轿厢\/乘客热源\/异常准星/, 'README should describe visual CCTV monitor, not only text logs');
});

test('android README reflects the current portable APK build flow', () => {
  assert.match(androidReadme, /npm run android:build/, 'Android README should use the supported build script');
  assert.match(androidReadme, /npm run android:inspect/, 'Android README should document APK metadata inspection');
  assert.match(androidReadme, /项目内便携工具链可构建/, 'Android README should reflect the verified portable toolchain');
  assert.match(androidReadme, /定制 launcher icon/, 'Android README should mention branded app icon');
  assert.match(androidReadme, /一屏内可玩/, 'Android README should document the one-screen mobile UX');
  assert.doesNotMatch(androidReadme, /当前环境缺少 Android 构建工具/, 'Android README must not keep stale blocker text');
});

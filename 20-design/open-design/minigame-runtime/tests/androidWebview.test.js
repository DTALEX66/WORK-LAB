import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const assets = resolve(root, 'android-webview/app/src/main/assets');
const androidMain = resolve(root, 'android-webview/app/src/main');
const pkg = JSON.parse(readFileSync(resolve(root, 'package.json'), 'utf8'));

test('android WebView assets use bundled script instead of ES modules', () => {
  execFileSync(process.execPath, ['scripts/prepare-android-webview.mjs'], { cwd: root, stdio: 'pipe' });
  const html = readFileSync(resolve(assets, 'index.html'), 'utf8');
  const css = readFileSync(resolve(assets, 'styles.css'), 'utf8');
  const game = readFileSync(resolve(assets, 'game.js'), 'utf8');

  assert.match(html, /<script src="game\.js"><\/script>/);
  assert.doesNotMatch(html, /type="module"/);
  assert.match(html, /user-scalable=no/);
  assert.match(game, /MINIGAME - Android WebView 小游戏构建/);
  assert.match(game, /document\.querySelector/);
  assert.match(game, /function loadArchive\(/, 'archive storage helper must be bundled before game.js');
  assert.match(game, /function getArchiveSkinProgress\(/, 'per-skin archive progress selector must be bundled');
  for (const asset of [
    'cctv-basement-lift-door-open-lite-loop.gif',
    'cctv-hospital-ward-native-lite-loop.gif',
    'cctv-security-room-native-lite-loop.gif',
    'cctv-factory-native-lite-loop.gif',
    'cctv-subway-platform-native-lite-loop.gif',
    'cctv-hotel-lobby-native-lite-loop.gif',
    'texture-control-panel.png',
    'texture-hud-glass.png',
  ]) {
    const markup = `${html}\n${css}`;
    assert.match(markup, new RegExp(asset.replace(/[.]/g, '\\.')), `Android WebView markup should reference generated asset ${asset}`);
    assert.equal(existsSync(resolve(assets, 'assets/generated', asset)), true, `Android WebView assets should include ${asset}`);
  }
  assert.doesNotMatch(game, /\bSKIN_DATA\b/);
  assert.doesNotMatch(game, /\b_getHiddenLog\b/);
});

test('android package exposes branded launcher name and icon resources', () => {
  const manifest = readFileSync(resolve(androidMain, 'AndroidManifest.xml'), 'utf8');
  const strings = readFileSync(resolve(androidMain, 'res/values/strings.xml'), 'utf8');
  const adaptiveIcon = readFileSync(resolve(androidMain, 'res/mipmap-anydpi-v26/ic_launcher.xml'), 'utf8');
  const foreground = readFileSync(resolve(androidMain, 'res/drawable/ic_launcher_foreground.xml'), 'utf8');

  assert.match(manifest, /android:label="@string\/app_name"/);
  assert.match(manifest, /android:icon="@mipmap\/ic_launcher"/);
  assert.match(manifest, /android:roundIcon="@mipmap\/ic_launcher_round"/);
  assert.match(strings, /<string name="app_name">异常电梯控制台<\/string>/);
  assert.match(adaptiveIcon, /<adaptive-icon/);
  assert.match(foreground, /#61FFBE/);
  assert.match(foreground, /#FF4D6D/);
});

test('android install script installs and launches the debug APK through adb', () => {
  const installScript = readFileSync(resolve(root, 'scripts/install-android-debug.mjs'), 'utf8');

  assert.equal(pkg.scripts['android:install'], 'node scripts/install-android-debug.mjs');
  assert.match(installScript, /adb devices -l/, 'script should show connected devices before installing');
  assert.match(installScript, /install', '-r'/, 'script should reinstall the debug APK');
  assert.match(installScript, /am', 'force-stop'/, 'script should restart the app from a clean state');
  assert.match(installScript, /am', 'start'/, 'script should launch MainActivity after install');
  assert.match(installScript, /com\.dtalex\.minigame\/.MainActivity/, 'script should launch the packaged activity');
});

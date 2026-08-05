import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');

const checks = [];

function addCheck(id, ok, level, message, detail = '') {
  checks.push({ id, ok, level, message, detail });
}

function readJson(relativePath) {
  const path = resolve(root, relativePath);
  return JSON.parse(readFileSync(path, 'utf8'));
}

function readJsonIfExists(relativePath) {
  const path = resolve(root, relativePath);
  if (!existsSync(path)) return null;
  return JSON.parse(readFileSync(path, 'utf8'));
}

function readText(relativePath) {
  return readFileSync(resolve(root, relativePath), 'utf8');
}

function isPlaceholder(value) {
  return typeof value !== 'string'
    || value.trim() === ''
    || /请替换|placeholder|xxxxx|your_|YOUR_|test-|demo-/i.test(value);
}

function extractAdUnits(configText) {
  const block = /adUnits:\s*{([\s\S]*?)\n\s*}/.exec(configText)?.[1] ?? '';
  const entries = [...block.matchAll(/(\w+):\s*['"]([^'"]+)['"]/g)];
  return Object.fromEntries(entries.map(([, key, value]) => [key, value]));
}

function runNode(label, args) {
  try {
    execFileSync(process.execPath, args, { cwd: root, encoding: 'utf8', stdio: 'pipe' });
    addCheck(label, true, 'blocker', `${label} passes`);
  } catch (error) {
    const output = `${error.stdout || ''}${error.stderr || ''}`.trim();
    addCheck(label, false, 'blocker', `${label} fails`, output);
  }
}

const releaseConfigPath = process.env.RELEASE_CONFIG_PATH || 'release.config.json';
const releaseConfig = readJsonIfExists(releaseConfigPath);
const wechatProject = readJson('wechat-minigame/project.config.json');
const wechatPrivateProject = readJsonIfExists('wechat-minigame/project.private.config.json');
const douyinProject = existsSync(resolve(root, 'douyin-minigame/project.config.json'))
  ? readJson('douyin-minigame/project.config.json')
  : null;
const douyinPrivateProject = readJsonIfExists('douyin-minigame/project.private.config.json');
const androidProject = existsSync(resolve(root, 'android-minigame/project.config.json'))
  ? readJson('android-minigame/project.config.json')
  : null;
const gameConfigText = readText('src/gameConfig.js');
const adUnits = releaseConfig?.adUnits ?? extractAdUnits(gameConfigText);
const wechatAppId = releaseConfig?.wechat?.appid ?? wechatPrivateProject?.appid ?? wechatProject.appid;
const douyinAppId = releaseConfig?.douyin?.appid ?? douyinPrivateProject?.appid ?? douyinProject?.appid;

addCheck(
  'wechatAppId',
  !isPlaceholder(wechatAppId),
  'blocker',
  'WeChat release config must provide a real Mini Game AppID',
  `current=${wechatAppId}`,
);

if (douyinProject || douyinAppId) {
  addCheck(
    'douyinAppId',
    !isPlaceholder(douyinAppId),
    'blocker',
    'Douyin release config must use a real Mini Game AppID',
    `current=${douyinAppId}`,
  );
}

if (androidProject) {
  addCheck(
    'androidMiniGameAppId',
    !isPlaceholder(androidProject.appid),
    'warning',
    'android-minigame project.config.json is a generated mini-game preview and still has a placeholder AppID',
    `current=${androidProject.appid}`,
  );
}

for (const key of ['revive', 'decode', 'truth']) {
  addCheck(
    `adUnit:${key}`,
    !isPlaceholder(adUnits[key]),
    'blocker',
    `CONFIG.adUnits.${key} must use a real rewarded-video ad unit id before release`,
    `current=${adUnits[key] ?? '<missing>'}`,
  );
}

runNode('wechatStrictBundle', ['build.js', 'wechat']);
try {
  execFileSync(process.execPath, ['scripts/check-wechat-bundle.mjs', '--strict'], {
    cwd: root,
    encoding: 'utf8',
    stdio: 'pipe',
  });
  addCheck('wechatBundleBlockers', true, 'blocker', 'WeChat bundle has no runtime blockers');
} catch (error) {
  const output = `${error.stdout || ''}${error.stderr || ''}`.trim();
  addCheck('wechatBundleBlockers', false, 'blocker', 'WeChat bundle has runtime blockers', output);
}

if (existsSync(resolve(root, 'android-webview/app/build/outputs/apk/debug/app-debug.apk'))) {
  try {
    execFileSync(process.execPath, ['scripts/check-apk-metadata.mjs'], {
      cwd: root,
      encoding: 'utf8',
      stdio: 'pipe',
    });
    addCheck('androidApkMetadata', true, 'blocker', 'Android APK metadata is valid');
  } catch (error) {
    const output = `${error.stdout || ''}${error.stderr || ''}`.trim();
    addCheck('androidApkMetadata', false, 'blocker', 'Android APK metadata check fails', output);
  }
} else {
  addCheck('androidApkMetadata', false, 'blocker', 'Android APK is missing; run npm run android:build first');
}

const failed = checks.filter(check => !check.ok);
const blockers = failed.filter(check => check.level === 'blocker');
const warnings = failed.filter(check => check.level === 'warning');

for (const check of checks) {
  const marker = check.ok ? 'PASS' : check.level.toUpperCase();
  console.log(`[${marker}] ${check.id}: ${check.message}`);
  if (!check.ok && check.detail) console.log(`  ${check.detail.split('\n').slice(0, 6).join('\n  ')}`);
}

console.log(`summary: ${checks.length - failed.length}/${checks.length} pass, ${warnings.length} warning(s), ${blockers.length} release blocker(s)`);

if (blockers.length > 0) {
  console.error('[release-check] Release is NOT ready. Replace placeholder AppID/adUnitId values before publishing.');
  process.exit(1);
}

console.log('[release-check] ✅ release checks passed');

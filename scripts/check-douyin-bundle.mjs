import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { extname, resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const projectDir = resolve(process.env.DOUYIN_PROJECT_DIR || resolve(root, 'douyin-minigame'));
const strict = process.argv.includes('--strict');
const checks = [];

function add(id, ok, level, message, detail = '') {
  checks.push({ id, ok, level, message, detail });
}

function readText(name) {
  const path = resolve(projectDir, name);
  return existsSync(path) ? readFileSync(path, 'utf8') : '';
}

function readJson(name) {
  try {
    return JSON.parse(readText(name));
  } catch {
    return null;
  }
}

function walk(dir) {
  if (!existsSync(dir)) return [];
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    if (entry.name.startsWith('.') || entry.name === 'node_modules') return [];
    const path = resolve(dir, entry.name);
    if (entry.isDirectory() && existsSync(resolve(path, '.douyin-local-workspace'))) return [];
    return entry.isDirectory() ? walk(path) : [path];
  });
}

const required = ['game.js', 'game.json', 'project.config.json'];
for (const file of required) {
  add(`required:${file}`, existsSync(resolve(projectDir, file)), 'blocker', `${file} exists`);
}

const bundle = readText('game.js');
const gameJson = readJson('game.json');
const projectConfig = readJson('project.config.json');
const projectPrivateConfig = readJson('project.private.config.json');
const effectiveAppId = projectPrivateConfig?.appid || projectConfig?.appid;
const files = walk(projectDir);
const packageBytes = files.reduce((sum, file) => sum + statSync(file).size, 0);
const allowedExtensions = new Set([
  '.js', '.json', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.txt', '.csv', '.xml',
  '.mp3', '.aac', '.m4a', '.wav', '.ogg', '.ttf', '.woff', '.otf', '.bin', '.wasm',
]);
const forbiddenFiles = files.filter(file => !allowedExtensions.has(extname(file).toLowerCase()));

add('syntaxTarget', bundle.includes('MINIGAME - 抖音 小游戏构建'), 'blocker', 'bundle has deterministic Douyin marker');
add('portraitFullscreen', gameJson?.deviceOrientation === 'portrait' && gameJson?.showStatusBar === false, 'blocker', 'game.json is portrait fullscreen');
add('compileType', projectConfig?.compileType === 'game', 'blocker', 'project is a game');
add('touristAppId', effectiveAppId !== 'touristappid', 'warning', 'real Douyin AppID is supplied only for release');
add('noDom', !/document\.(querySelector|createElement)|window\.(addEventListener|setInterval|clearInterval)/.test(bundle), 'blocker', 'bundle has no DOM/BOM dependency');
add('ttHost', /typeof tt !== ['"]undefined['"]/.test(bundle), 'blocker', 'bundle detects the tt host');
add('canvasRuntime', /createCanvas/.test(bundle) && /getCanvasLayout/.test(bundle), 'blocker', 'Canvas runtime is bundled');
add('explicitStart', /createMiniGameClock/.test(bundle) && /getCanvasStartControls/.test(bundle), 'blocker', 'countdown waits for explicit start');
add('noDebugTrigger', !/forceAnomaly/.test(bundle), 'blocker', 'production bundle excludes forced-anomaly debug controls');
add('lifecycle', /\.onHide\?\.|\.onHide\(|onHide\?\./.test(bundle) && /\.onShow\?\.|\.onShow\(|onShow\?\./.test(bundle), 'blocker', 'foreground/background lifecycle is handled');
add('sidebarRevisit', /checkScene\s*\(/.test(bundle) && /navigateToScene\s*\(/.test(bundle) && /scene:\s*['"]sidebar['"]/.test(bundle), 'blocker', 'mandatory sidebar check and revisit calls are present');
add('rewardedAd', /createRewardedVideoAd/.test(bundle) && /isEnded/.test(bundle) && /function shouldApplyReward\s*\(/.test(bundle), 'blocker', 'rewarded video requires completed close and includes the reward guard implementation');
add('packageBytes', packageBytes <= 20 * 1024 * 1024, 'blocker', `packageBytes=${packageBytes} is within 20MB`);
add('fileTypes', forbiddenFiles.length === 0, 'blocker', 'all package file types are allowed', forbiddenFiles.join('\n'));

const failures = checks.filter(check => !check.ok);
const blockers = failures.filter(check => check.level === 'blocker');
const warnings = failures.filter(check => check.level === 'warning');
for (const check of checks) {
  const marker = check.ok ? 'PASS' : check.level.toUpperCase();
  console.log(`[${marker}] ${check.id}: ${check.message}`);
  if (!check.ok && check.detail) console.log(`  ${check.detail}`);
}
console.log(`summary: ${checks.length - failures.length}/${checks.length} pass, warning(s): ${warnings.length}, runtime blocker(s): ${blockers.length}`);
if (strict && blockers.length > 0) process.exitCode = 1;

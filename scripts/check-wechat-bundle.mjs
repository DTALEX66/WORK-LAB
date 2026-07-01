import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '..');
const bundlePath = resolve(root, 'wechat-minigame', 'game.js');
const gameJsonPath = resolve(root, 'wechat-minigame', 'game.json');
const projectConfigPath = resolve(root, 'wechat-minigame', 'project.config.json');

const bundle = readFileSync(bundlePath, 'utf8');
const gameJson = JSON.parse(readFileSync(gameJsonPath, 'utf8'));
const projectConfig = JSON.parse(readFileSync(projectConfigPath, 'utf8'));

const checks = [
  {
    id: 'syntaxTarget',
    ok: bundle.includes('MINIGAME - 微信 小游戏构建'),
    level: 'pass',
    message: 'bundle has deterministic WeChat build marker',
  },
  {
    id: 'gameJsonPortrait',
    ok: gameJson.deviceOrientation === 'portrait' && gameJson.showStatusBar === false,
    level: 'pass',
    message: 'game.json keeps portrait fullscreen settings',
  },
  {
    id: 'compileType',
    ok: projectConfig.compileType === 'game',
    level: 'pass',
    message: 'project.config.json compileType is game',
  },
  {
    id: 'placeholderAppId',
    ok: projectConfig.appid !== '请替换为你的微信小游戏 AppID',
    level: 'warning',
    message: 'project.config.json should use a real WeChat Mini Game AppID before release',
  },
  {
    id: 'domDependency',
    ok: !/document\.(querySelector|createElement)/.test(bundle),
    level: 'blocker',
    message: 'bundle must not contain DOM APIs; real WeChat runtime has no document',
  },
  {
    id: 'windowDependency',
    ok: !/window\.(addEventListener|setInterval|clearInterval)/.test(bundle),
    level: 'blocker',
    message: 'bundle must not contain browser window APIs; real WeChat runtime needs Canvas runtime',
  },
  {
    id: 'hiddenLogAlias',
    ok: !bundle.includes('_getHiddenLog('),
    level: 'blocker',
    message: 'bundle must not reference stripped import alias _getHiddenLog',
  },
  {
    id: 'canvasRenderer',
    ok: bundle.includes('canvasRenderer.js') || bundle.includes('getCanvasActionButtons'),
    level: 'blocker',
    message: 'bundle must include the Canvas renderer entry used by mini-game platforms',
  },
];

const failures = checks.filter(check => !check.ok);
const blockers = failures.filter(check => check.level === 'blocker');
const warnings = failures.filter(check => check.level === 'warning');

for (const check of checks) {
  const marker = check.ok ? 'PASS' : check.level.toUpperCase();
  console.log(`[${marker}] ${check.id}: ${check.message}`);
}

console.log(`summary: ${checks.length - failures.length}/${checks.length} pass, ${warnings.length} warning(s), ${blockers.length} blocker(s)`);

if (process.argv.includes('--strict') && blockers.length > 0) {
  process.exitCode = 1;
}

import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import test from 'node:test';

const manifestPath = new URL('../games/find-anomaly/elevator-console/game.manifest.json', import.meta.url);
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
const rootReadme = readFileSync(new URL('../README.md', import.meta.url), 'utf8');
const positioning = readFileSync(new URL('../docs/PLATFORM_POSITIONING.md', import.meta.url), 'utf8');
const directoryMap = readFileSync(new URL('../docs/DIRECTORY_MAP.md', import.meta.url), 'utf8');

test('MINIGAME is positioned as a minigame collection platform', () => {
  assert.match(rootReadme, /小游戏合集平台/, 'README should state the platform positioning');
  assert.match(positioning, /小游戏合集平台 \+ AI 生产系统/, 'positioning doc should define the new platform role');
  assert.match(directoryMap, /games\/<category>\/<game-id>/, 'directory map should define category/game directory convention');
});

test('launch game is categorized as find-anomaly with a manifest', () => {
  assert.equal(manifest.id, 'find-anomaly.elevator-console');
  assert.equal(manifest.category, 'find-anomaly');
  assert.equal(manifest.categoryName, '找异常');
  assert.equal(manifest.platformRole, 'launch-game');
  assert.ok(manifest.buildTargets.includes('wechat-minigame'));
  assert.ok(manifest.buildTargets.includes('douyin-minigame'));
  assert.ok(manifest.contentPacks.includes('elevator'));
  assert.ok(existsSync(new URL('../games/find-anomaly/elevator-console/runtime-map.md', import.meta.url)));
});

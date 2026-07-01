import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const assets = resolve(root, 'android-webview/app/src/main/assets');

test('android WebView assets use bundled script instead of ES modules', () => {
  execFileSync(process.execPath, ['scripts/prepare-android-webview.mjs'], { cwd: root, stdio: 'pipe' });
  const html = readFileSync(resolve(assets, 'index.html'), 'utf8');
  const game = readFileSync(resolve(assets, 'game.js'), 'utf8');

  assert.match(html, /<script src="game\.js"><\/script>/);
  assert.doesNotMatch(html, /type="module"/);
  assert.match(html, /user-scalable=no/);
  assert.match(game, /MINIGAME - 抖音 小游戏构建|MINIGAME - android 小游戏构建/);
  assert.match(game, /document\.querySelector/);
  assert.doesNotMatch(game, /\bSKIN_DATA\b/);
  assert.doesNotMatch(game, /\b_getHiddenLog\b/);
});

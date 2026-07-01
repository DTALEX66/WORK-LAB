import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const output = resolve(root, 'wechat-minigame', 'game.js');

test('wechat build output is deterministic across repeated runs', () => {
  execFileSync(process.execPath, ['build.js', 'wechat'], { cwd: root, stdio: 'pipe' });
  const first = readFileSync(output, 'utf8');

  execFileSync(process.execPath, ['build.js', 'wechat'], { cwd: root, stdio: 'pipe' });
  const second = readFileSync(output, 'utf8');

  assert.equal(second, first);
});

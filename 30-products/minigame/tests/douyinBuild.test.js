import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import test from 'node:test';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');

test('douyin strict checker accepts the generated Canvas project', () => {
  execFileSync(process.execPath, ['build.js', 'douyin'], { cwd: root, stdio: 'pipe' });
  const output = execFileSync(process.execPath, ['scripts/check-douyin-bundle.mjs', '--strict'], {
    cwd: root,
    encoding: 'utf8',
  });
  assert.match(output, /runtime blocker\(s\): 0/);
  assert.match(output, /packageBytes/);
});

test('douyin compliance checker validates privacy, age-rating and sensitive API inventory', () => {
  execFileSync(process.execPath, ['build.js', 'douyin'], { cwd: root, stdio: 'pipe' });
  const output = execFileSync(process.execPath, ['scripts/check-douyin-compliance.mjs', '--strict'], {
    cwd: root,
    encoding: 'utf8',
  });
  assert.match(output, /code blocker\(s\): 0/);
  assert.match(output, /external placeholder\(s\): 2/);
  assert.match(output, /ageRating16Plus/);
  assert.match(output, /reviewAdPaths/);
});

test('Douyin release package injects the private appid into the archived project config', () => {
  const source = readFileSync(resolve(root, 'scripts', 'package-douyin-release.mjs'), 'utf8');
  assert.match(source, /projectConfig\.appid\s*=\s*privateConfig\.appid/);
  assert.match(source, /release package requires a real Douyin appid/);
});

test('douyin strict checker rejects a known-broken project', () => {
  const broken = resolve(root, '.tmp', 'douyin-broken');
  rmSync(broken, { recursive: true, force: true });
  mkdirSync(broken, { recursive: true });
  writeFileSync(resolve(broken, 'game.js'), 'tt.createCanvas();');
  writeFileSync(resolve(broken, 'game.json'), JSON.stringify({ deviceOrientation: 'portrait' }));
  writeFileSync(resolve(broken, 'project.config.json'), JSON.stringify({ compileType: 'game', appid: 'touristappid' }));

  assert.throws(() => execFileSync(process.execPath, ['scripts/check-douyin-bundle.mjs', '--strict'], {
    cwd: root,
    env: { ...process.env, DOUYIN_PROJECT_DIR: broken },
    stdio: 'pipe',
  }));
  rmSync(broken, { recursive: true, force: true });
});

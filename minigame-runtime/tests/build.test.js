import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const output = resolve(root, 'wechat-minigame', 'game.js');
const privateConfigOutput = resolve(root, 'wechat-minigame', 'project.private.config.json');
const tempDir = resolve(root, '.tmp');
const tempReleaseConfig = resolve(tempDir, 'release-test.config.json');

test('wechat build output is deterministic across repeated runs', () => {
  execFileSync(process.execPath, ['build.js', 'wechat'], { cwd: root, stdio: 'pipe' });
  const first = readFileSync(output, 'utf8');

  execFileSync(process.execPath, ['build.js', 'wechat'], { cwd: root, stdio: 'pipe' });
  const second = readFileSync(output, 'utf8');

  assert.equal(second, first);
});

test('release config can inject private AppID and ad units into generated files', () => {
  mkdirSync(tempDir, { recursive: true });
  writeFileSync(tempReleaseConfig, JSON.stringify({
    wechat: {
      appid: 'wx_real_release_test_appid',
      projectname: 'MINIGAME_TEST',
    },
    adUnits: {
      revive: 'adunit-real-revive-test',
      decode: 'adunit-real-decode-test',
      truth: 'adunit-real-truth-test',
    },
  }, null, 2));

  try {
    execFileSync(process.execPath, ['build.js', 'wechat'], {
      cwd: root,
      env: { ...process.env, RELEASE_CONFIG_PATH: tempReleaseConfig },
      stdio: 'pipe',
    });

    const bundle = readFileSync(output, 'utf8');
    const privateConfig = JSON.parse(readFileSync(privateConfigOutput, 'utf8'));
    const sourceConfig = readFileSync(resolve(root, 'src/gameConfig.js'), 'utf8');
    const gitignore = readFileSync(resolve(root, '.gitignore'), 'utf8');

    assert.match(bundle, /adunit-real-revive-test/);
    assert.match(bundle, /adunit-real-decode-test/);
    assert.match(bundle, /adunit-real-truth-test/);
    assert.equal(privateConfig.appid, 'wx_real_release_test_appid');
    assert.equal(privateConfig.projectname, 'MINIGAME_TEST');
    assert.match(sourceConfig, /adunit-xxxxx_revive/, 'source config should keep safe placeholder values');
    assert.match(gitignore, /release\.config\.json/);
    assert.match(gitignore, /wechat-minigame\/project\.private\.config\.json/);
  } finally {
    if (existsSync(privateConfigOutput)) rmSync(privateConfigOutput, { force: true });
    if (existsSync(tempReleaseConfig)) rmSync(tempReleaseConfig, { force: true });
    execFileSync(process.execPath, ['build.js', 'wechat'], { cwd: root, stdio: 'pipe' });
  }
});

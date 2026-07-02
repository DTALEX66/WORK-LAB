#!/usr/bin/env node
/*
 * verify-all.cjs — one-command project acceptance gate.
 *
 * Kept CommonJS so `npm run verify` still starts on Windows machines where
 * WeChat DevTools' Node 16 appears first on PATH. Commands that need modern
 * Node are dispatched through the Hermes bundled Node executable.
 */
const { existsSync } = require('node:fs');
const { join } = require('node:path');
const { spawnSync } = require('node:child_process');

const summaryMode = process.argv.includes('--summary');

function parseMajor(version) {
  const match = /^v?(\d+)/.exec(version || '');
  return match ? Number(match[1]) : 0;
}

function candidateNodes() {
  const candidates = [process.execPath];
  if (process.env.HERMES_NODE) candidates.push(process.env.HERMES_NODE);
  if (process.env.LOCALAPPDATA) {
    candidates.push(join(process.env.LOCALAPPDATA, 'hermes', 'node', 'node.exe'));
  }
  if (process.env.USERPROFILE) {
    candidates.push(join(process.env.USERPROFILE, 'AppData', 'Local', 'hermes', 'node', 'node.exe'));
  }
  return [...new Set(candidates)].filter(Boolean);
}

function nodeVersion(executable) {
  const result = spawnSync(executable, ['--version'], { encoding: 'utf8' });
  if (result.status !== 0) return null;
  return (result.stdout || result.stderr || '').trim();
}

function findModernNode() {
  for (const executable of candidateNodes()) {
    if (!existsSync(executable)) continue;
    const version = nodeVersion(executable);
    if (parseMajor(version) >= 20) return { executable, version };
  }
  return null;
}

function run(label, command, args, options = {}) {
  if (!summaryMode) console.log(`\n[verify] === ${label} ===`);
  const result = spawnSync(command, args, {
    cwd: process.cwd(),
    env: process.env,
    stdio: summaryMode ? 'pipe' : 'inherit',
    shell: false,
    windowsHide: true,
    encoding: summaryMode ? 'utf8' : undefined,
    ...options,
  });
  if (result.error) {
    console.error(`[verify] ${label} failed to start: ${result.error.message}`);
    process.exit(1);
  }
  if (result.status !== 0) {
    console.error(`[verify] ${label} failed with exit code ${result.status}`);
    process.exit(result.status || 1);
  }
  return result;
}

function printSummary(message) {
  if (summaryMode) console.log(message);
}

const modern = findModernNode();
if (!modern) {
  console.error('[verify] Node >=20 not found. Set HERMES_NODE or install Hermes bundled Node.');
  console.error('[verify] Current Node:', process.version, process.execPath);
  process.exit(1);
}

if (!summaryMode) console.log(`[verify] using modern Node ${modern.version} at ${modern.executable}`);

run('unit/regression tests', modern.executable, ['scripts/run-tests.cjs']);
printSummary('[verify] tests: pass');
run('WeChat mini-game build', modern.executable, ['build.js', 'wechat']);
run('WeChat strict bundle check', modern.executable, ['scripts/check-wechat-bundle.mjs', '--strict']);
printSummary('[verify] wechat strict: 0 blocker');
run('Android debug APK build', modern.executable, ['scripts/build-android-debug.mjs']);
printSummary('[verify] android build: OK');
run('Android APK metadata inspection', modern.executable, ['scripts/check-apk-metadata.mjs']);
printSummary('[verify] apk metadata: OK');

if (!summaryMode) console.log('\n[verify] ✅ all checks passed');

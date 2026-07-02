#!/usr/bin/env node
/*
 * run-tests.cjs — Node 16 compatible test launcher.
 *
 * Some Windows dev machines put the WeChat DevTools Node 16 first on PATH.
 * Node 16 does not support `node --test`, so `npm test` must bootstrap a
 * modern Node executable before invoking the real Node test runner.
 */
const { existsSync } = require('node:fs');
const { join } = require('node:path');
const { spawnSync } = require('node:child_process');

function parseMajor(version) {
  const match = /^v?(\d+)/.exec(version || '');
  return match ? Number(match[1]) : 0;
}

function candidateNodes() {
  const candidates = [process.execPath];

  if (process.env.HERMES_NODE) candidates.push(process.env.HERMES_NODE);

  const localAppData = process.env.LOCALAPPDATA;
  if (localAppData) {
    candidates.push(join(localAppData, 'hermes', 'node', 'node.exe'));
  }

  const home = process.env.USERPROFILE;
  if (home) {
    candidates.push(join(home, 'AppData', 'Local', 'hermes', 'node', 'node.exe'));
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

const modern = findModernNode();
if (!modern) {
  console.error('[test] Node >=20 is required for node:test glob execution.');
  console.error('[test] Current Node:', process.version, process.execPath);
  console.error('[test] Install/update Hermes bundled Node or set HERMES_NODE to a modern node.exe.');
  process.exit(1);
}

const args = ['--test', '--test-concurrency=1', 'tests/*.test.js'];
console.log(`[test] using ${modern.version} at ${modern.executable}`);
const result = spawnSync(modern.executable, args, {
  stdio: 'inherit',
  shell: false,
  windowsHide: true,
});

if (result.error) {
  console.error('[test] failed to launch test runner:', result.error.message);
  process.exit(1);
}
process.exit(result.status ?? 1);

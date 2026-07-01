import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const pkg = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
const launcher = readFileSync(new URL('../scripts/run-tests.cjs', import.meta.url), 'utf8');

test('npm test uses a Node16-compatible launcher', () => {
  assert.equal(pkg.scripts.test, 'node scripts/run-tests.cjs');
  assert.match(launcher, /findModernNode/, 'launcher should locate a modern bundled Node');
  assert.match(launcher, /LOCALAPPDATA/, 'launcher should support Hermes bundled Node on Windows');
  assert.match(launcher, /--test/, 'launcher should invoke the real node:test runner');
});

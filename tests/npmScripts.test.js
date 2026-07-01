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

test('android inspect script verifies APK launcher metadata', () => {
  const inspectScript = readFileSync(new URL('../scripts/check-apk-metadata.mjs', import.meta.url), 'utf8');

  assert.equal(pkg.scripts['android:inspect'], 'node scripts/check-apk-metadata.mjs');
  assert.match(inspectScript, /dump', 'badging'/, 'script should inspect APK badging via aapt');
  assert.match(inspectScript, /application-label:'\$\{expected\.label\}'/, 'script should assert launcher label');
  assert.match(inspectScript, /launcher icon is branded ic_launcher resource/, 'script should assert launcher icon resource');
});

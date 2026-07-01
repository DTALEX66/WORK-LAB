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

test('verify script runs the full release acceptance gate', () => {
  const verifyScript = readFileSync(new URL('../scripts/verify-all.cjs', import.meta.url), 'utf8');

  assert.equal(pkg.scripts.verify, 'node scripts/verify-all.cjs');
  assert.match(verifyScript, /npmCommand\(\), \['test'\]/, 'verify should run npm test');
  assert.match(verifyScript, /\['build\.js', 'wechat'\]/, 'verify should build WeChat bundle');
  assert.match(verifyScript, /check-wechat-bundle\.mjs', '--strict'/, 'verify should run WeChat strict check');
  assert.match(verifyScript, /build-android-debug\.mjs/, 'verify should build Android APK');
  assert.match(verifyScript, /check-apk-metadata\.mjs/, 'verify should inspect APK metadata');
});

test('release check blocks placeholder publishing configuration', () => {
  const releaseScript = readFileSync(new URL('../scripts/check-release-readiness.mjs', import.meta.url), 'utf8');

  assert.equal(pkg.scripts['release:check'], 'node scripts/check-release-readiness.mjs');
  assert.match(releaseScript, /wechatAppId/, 'release check should validate WeChat AppID');
  assert.match(releaseScript, /CONFIG\.adUnits\.\$\{key\}/, 'release check should validate rewarded-video ad units');
  assert.match(releaseScript, /Release is NOT ready/, 'release check should fail closed when blockers exist');
  assert.match(releaseScript, /wechatBundleBlockers/, 'release check should include runtime bundle blockers');
  assert.match(releaseScript, /androidApkMetadata/, 'release check should include Android APK metadata');
});

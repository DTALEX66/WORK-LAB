import assert from 'node:assert/strict';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { relative } from 'node:path';
import test from 'node:test';

const root = new URL('../', import.meta.url);
const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');
const readme = readFileSync(new URL('../games/find-anomaly/elevator-console/README.md', import.meta.url), 'utf8');
const runtimeMap = readFileSync(new URL('../games/find-anomaly/elevator-console/runtime-map.md', import.meta.url), 'utf8');
const canvasAssets = readFileSync(new URL('../platform/canvasAssets.js', import.meta.url), 'utf8');
const gameAssetsRoot = new URL('../games/find-anomaly/elevator-console/assets/', import.meta.url);
const visualAssetsRoot = new URL('../games/find-anomaly/elevator-console/assets/abnormal_elevator_visual_assets/', import.meta.url);
const uiKitRoot = new URL('../games/find-anomaly/elevator-console/assets/abnormal_elevator_ui_kit/', import.meta.url);

function listFiles(dirUrl) {
  const files = [];
  for (const entry of readdirSync(dirUrl)) {
    const child = new URL(`${entry}`, dirUrl);
    const stats = statSync(child);
    if (stats.isDirectory()) {
      files.push(...listFiles(new URL(`${entry}/`, dirUrl)));
    } else {
      files.push(child);
    }
  }
  return files;
}

function filename(fileUrl) {
  return decodeURIComponent(fileUrl.pathname.split('/').pop());
}

test('imported first-game asset pack lives under the elevator game directory', () => {
  const allImportedFiles = listFiles(gameAssetsRoot);
  assert.equal(allImportedFiles.length, 77);
  for (const file of allImportedFiles) {
    const relativePath = relative(root.pathname.slice(1), file.pathname.slice(1)).replaceAll('\\', '/');
    assert.match(relativePath, /^games\/find-anomaly\/elevator-console\/assets\//);
  }
});

test('all runtime-ready visual PNGs are wired into their CSS or Canvas runtime', () => {
  const visualFiles = listFiles(visualAssetsRoot);
  const runtimePngs = visualFiles.filter(file => filename(file).endsWith('.png'));
  const v5Pngs = runtimePngs.filter(file => filename(file).startsWith('v5_'));
  const legacyPngs = runtimePngs.filter(file => !filename(file).startsWith('v5_'));

  assert.equal(legacyPngs.length, 62);
  assert.equal(v5Pngs.length, 8);
  for (const file of legacyPngs) {
    assert.match(css, new RegExp(filename(file).replace(/[.]/g, '\\.')), `${filename(file)} should be wired into runtime CSS`);
  }
  for (const file of v5Pngs) {
    assert.match(canvasAssets, new RegExp(filename(file).replace(/[.]/g, '\\.')), `${filename(file)} should be wired into Canvas assets`);
  }
});

test('reference-only imported files stay out of runtime CSS and are documented', () => {
  for (const file of listFiles(uiKitRoot)) {
    assert.doesNotMatch(css, new RegExp(filename(file).replace(/[.]/g, '\\.')), `${filename(file)} should stay reference-only`);
  }
  for (const referenceOnly of ['abnormal-elevator-ui-kit.html']) {
    assert.doesNotMatch(css, new RegExp(referenceOnly.replace(/[.]/g, '\\.')), `${referenceOnly} should not be loaded as runtime UI`);
  }
  assert.match(readme, /资源接入状态/);
  assert.match(runtimeMap, /当前接入范围/);
});

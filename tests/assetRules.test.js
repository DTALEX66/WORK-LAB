import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import test from 'node:test';

const generatedAssets = readdirSync(new URL('../assets/generated/', import.meta.url));
const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');
const rules = readFileSync(new URL('../docs/ASSET_RULES.md', import.meta.url), 'utf8');

test('asset rules require text-free backgrounds and rendered UI copy', () => {
  assert.match(rules, /背景图不允许带文字/, 'rules should forbid text baked into background images');
  assert.match(rules, /UI 文字.*HTML\/Canvas 渲染/, 'rules should require UI copy to be rendered by HTML/Canvas');
  assert.match(rules, /OCR|文字|水印|logo/i, 'rules should mention rejection of OCR/text/watermark/logo artifacts');
});

test('CSS background assets do not use UI reference screens as game backgrounds', () => {
  assert.doesNotMatch(css, /url\("assets\/generated\/ui-reference-[^)]+"\)/, 'reference screenshots must not be used as in-game background layers');
});

test('generated background asset filenames avoid text-bearing source intent', () => {
  const backgroundLike = generatedAssets.filter(name => /^(cctv|monitor|texture|overlay)-/.test(name));
  assert.ok(backgroundLike.length > 0, 'should have generated background/overlay assets to check');
  for (const name of backgroundLike) {
    assert.doesNotMatch(name, /(?:^|[-_])(text|word|logo|label|caption|title|watermark)(?:[-_.]|$)/i, `${name} should not advertise baked-in text or logos`);
  }
});

test('processed elevator CCTV assets are named as text-free scene states', () => {
  for (const name of [
    'cctv-elevator-corridor-clear.png',
    'cctv-elevator-corridor-warp.png',
    'cctv-elevator-corridor-figure.png',
  ]) {
    assert.ok(generatedAssets.includes(name), `${name} should exist in generated assets`);
    assert.doesNotMatch(name, /Gemini|Generated|watermark|logo|text/i, `${name} should be renamed away from source/watermark terms`);
  }
});

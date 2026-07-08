import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');
const gameSource = readFileSync(new URL('../src/game.js', import.meta.url), 'utf8');

test('CCTV stage exposes dedicated anomaly feedback layers', () => {
  for (const className of ['signal-tear-layer', 'freeze-frame', 'infrared-flicker', 'snow-burst']) {
    assert.match(html, new RegExp(`class="${className}"`), `${className} should be rendered by HTML, not baked into the image`);
  }
});

test('data-anomaly active enables tear freeze infrared flicker and stronger snow', () => {
  assert.match(css, /\.monitor\[data-anomaly="active"\][\s\S]*\.signal-tear-layer/, 'active anomaly should enable signal tear layer');
  assert.match(css, /\.monitor\[data-anomaly="active"\][\s\S]*\.freeze-frame/, 'active anomaly should enable short freeze layer');
  assert.match(css, /\.monitor\[data-anomaly="active"\][\s\S]*\.infrared-flicker/, 'active anomaly should enable infrared flicker layer');
  assert.match(css, /\.monitor\[data-anomaly="active"\][\s\S]*\.snow-burst/, 'active anomaly should enable intensified snow layer');
  for (const keyframe of ['signalTearBurst', 'cctvFreezeFrame', 'infraredFlicker', 'signalSnowBurst']) {
    assert.match(css, new RegExp(`@keyframes\\s+${keyframe}`), `${keyframe} animation should exist`);
  }
});

test('elevator CCTV feed switches between processed calm anomaly and danger assets', () => {
  assert.match(css, /--cctv-feed:\s*url\("assets\/generated\/cctv-elevator-corridor-clear\.png"\)/, 'calm elevator feed should use the processed clear corridor asset');
  assert.match(css, /--cctv-feed-anomaly:\s*url\("assets\/generated\/cctv-elevator-corridor-warp\.png"\)/, 'active anomaly should have a processed warped corridor asset');
  assert.match(css, /--cctv-feed-danger:\s*url\("assets\/generated\/cctv-elevator-corridor-figure\.png"\)/, 'critical/danger anomaly should have a processed figure corridor asset');
  assert.match(css, /\.monitor\[data-anomaly="active"\] \.cctv-stage[\s\S]*--cctv-feed:\s*var\(--cctv-feed-anomaly\)/, 'active anomaly should switch CCTV feed to anomaly asset');
  assert.match(css, /\.console-shell\[data-tone="critical"\] \.monitor\[data-anomaly="active"\] \.cctv-stage,[\s\S]*\.console-shell\[data-tone="danger"\] \.monitor\[data-anomaly="active"\] \.cctv-stage[\s\S]*--cctv-feed:\s*var\(--cctv-feed-danger\)/, 'critical/danger active anomaly should switch CCTV feed to figure asset');
});

test('DOM renderer applies visualState datasets and highlighted action', () => {
  assert.match(gameSource, /deriveVisualState/, 'game should derive visual state from GameState');
  assert.match(gameSource, /dataset\.glitch/, 'monitor should expose visualState glitch as a dataset');
  assert.match(gameSource, /dataset\.shake/, 'monitor should expose visualState shake as a dataset');
  assert.match(gameSource, /style\.setProperty\('--cctv-noise'/, 'noise intensity should flow into CSS variable');
  assert.match(gameSource, /dataset\.recommended\s*=\s*String\(visual\.highlightAction === action\.id\)/, 'recommended action should be reflected on buttons');
});

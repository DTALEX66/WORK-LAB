import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');
const gameSource = readFileSync(new URL('../src/game.js', import.meta.url), 'utf8');

const CCTV_STATE_IDS = [
  '00_idle_closed',
  '01_door_open',
  '02_door_opening',
  '03_door_closing',
  '04_moving_up',
  '05_moving_down',
  '06_power_low',
  '07_power_outage',
  '08_emergency_stop',
  '09_door_jammed',
  '10_signal_lost',
  '11_camera_glitch',
  '12_scan_active',
  '13_entity_near',
  '14_shadow_inside',
  '15_anomaly_wandering',
  '16_wrong_floor',
  '17_loop_corridor',
  '18_locked',
  '19_stabilized',
  '20_threat_high',
  '21_maintenance_mode',
  '22_system_reboot',
  '23_cooldown_safe',
];

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

test('clear CCTV establishes a clean baseline before anomaly-specific entities appear', () => {
  for (const className of ['door-gap-glow', 'distant-shadow', 'thermal-ghost', 'detection-corners', 'cctv-loop']) {
    assert.match(css, new RegExp(`\\.${className}\\s*\\{[\\s\\S]*?opacity:\\s*0(?:[;\\s])`), `${className} should be hidden in clear state`);
  }
  assert.match(css, /\.monitor\[data-anomaly="active"\] \.cctv-loop[\s\S]*opacity:\s*0\.[1-9]/, 'active anomaly should reveal the animated CCTV target');
});

test('elevator CCTV feed switches between processed calm anomaly and danger assets', () => {
  assert.match(css, /--cctv-feed:\s*url\("games\/find-anomaly\/elevator-console\/assets\/abnormal_elevator_visual_assets\/cctv_states\/00_idle_closed\.png"\)/, 'calm elevator feed should use the first-game imported closed-door asset');
  assert.match(css, /--cctv-feed-anomaly:\s*url\("games\/find-anomaly\/elevator-console\/assets\/abnormal_elevator_visual_assets\/cctv_states\/11_camera_glitch\.png"\)/, 'active anomaly should use the first-game imported camera glitch asset');
  assert.match(css, /--cctv-feed-danger:\s*url\("games\/find-anomaly\/elevator-console\/assets\/abnormal_elevator_visual_assets\/cctv_states\/20_threat_high\.png"\)/, 'critical/danger anomaly should use the first-game imported high-threat asset');
  assert.match(css, /\.monitor\[data-anomaly="active"\] \.cctv-stage[\s\S]*--cctv-feed:\s*var\(--cctv-feed-anomaly\)/, 'active anomaly should switch CCTV feed to anomaly asset');
  assert.match(css, /\.console-shell\[data-tone="critical"\] \.monitor\[data-anomaly="active"\] \.cctv-stage,[\s\S]*\.console-shell\[data-tone="danger"\] \.monitor\[data-anomaly="active"\] \.cctv-stage[\s\S]*--cctv-feed:\s*var\(--cctv-feed-danger\)/, 'critical/danger active anomaly should switch CCTV feed to figure asset');
});

test('imported visual kit skins CCTV frame and hardware buttons without baking copy into images', () => {
  for (const asset of [
    'overlay_cctv_frame.png',
    'overlay_glitch_blocks.png',
    'overlay_red_alert_frame.png',
    'overlay_scanlines.png',
    'overlay_scan_sweep.png',
    'overlay_vignette.png',
    'btn_close_default.png',
    'btn_up_recommended.png',
    'btn_stop_danger.png',
    'btn_log_secondary.png',
    'btn_more_secondary.png',
  ]) {
    assert.match(css, new RegExp(asset.replace(/[.]/g, '\\.')), `CSS should reference imported visual kit asset ${asset}`);
  }
  assert.match(css, /\.actions button,[\s\S]*\.secondary-actions button,[\s\S]*\.more-actions-button[\s\S]*--action-button-sprite/, 'hardware buttons should use sprite-backed skins');
  assert.match(gameSource, /className\s*=\s*'action-label'/, 'readable action copy should remain DOM-rendered');
});

test('all imported CCTV state images have desktop and mobile runtime hooks', () => {
  for (const id of CCTV_STATE_IDS) {
    assert.match(css, new RegExp(`cctv_states/${id}\\.png`), `desktop CCTV state ${id} should be referenced`);
    assert.match(css, new RegExp(`mobile_cctv_states/${id}_mobile\\.png`), `mobile CCTV state ${id} should be referenced`);
    assert.match(css, new RegExp(`data-cctv-state="${id}"`), `runtime CSS selector should exist for ${id}`);
  }
});

test('DOM renderer applies visualState datasets and highlighted action', () => {
  assert.match(gameSource, /deriveVisualState/, 'game should derive visual state from GameState');
  assert.match(gameSource, /dataset\.glitch/, 'monitor should expose visualState glitch as a dataset');
  assert.match(gameSource, /dataset\.shake/, 'monitor should expose visualState shake as a dataset');
  assert.match(gameSource, /dataset\.cctvState\s*=\s*visual\.cctvState/, 'monitor should expose imported CCTV state as a dataset');
  assert.match(gameSource, /style\.setProperty\('--cctv-noise'/, 'noise intensity should flow into CSS variable');
  assert.match(gameSource, /dataset\.recommended\s*=\s*String\(visual\.highlightAction === action\.id\)/, 'recommended action should be reflected on buttons');
});

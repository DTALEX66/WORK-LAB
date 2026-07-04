import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');
const js = readFileSync(new URL('../src/game.js', import.meta.url), 'utf8');
const previewServer = readFileSync(new URL('../scripts/preview-server.mjs', import.meta.url), 'utf8');

test('CCTV GIF is the primary play surface', () => {
  assert.match(html, /class="[^"]*\bcctv-monitor\b/, 'preview should expose a CCTV monitor surface');
  assert.match(html, /class="[^"]*\bcctv-gif\b[^"]*"[^>]+data-cctv-gif/, 'monitor should load the animated CCTV GIF');
  assert.match(html, /assets\/generated\/cctv-basement-lift-door-open-lite-loop\.gif/, 'real elevator door opening GIF should be referenced from generated assets');
  assert.match(html, /class="cctv-fallback"/, 'monitor should provide a still fallback layer');
  assert.match(css, /\.cctv-monitor[\s\S]*min-height:\s*560px/, 'desktop CCTV should dominate the play surface');
  assert.match(css, /\.cctv-gif[\s\S]*object-fit:\s*cover/, 'GIF should fill the monitor without distortion');
  assert.match(css, /\.console-shell\.game-shell \.cctv-gif[\s\S]*z-index:\s*2/, 'GIF layer should sit above the still fallback');
  assert.match(css, /\.console-shell\.game-shell \.cctv-fallback[\s\S]*z-index:\s*0/, 'fallback layer should stay behind the GIF');
  assert.match(css, /\.cctv-fallback[\s\S]*var\(--cctv-feed\)/, 'CSS fallback should also use the animated CCTV feed');
});

test('CCTV overlays are diegetic and anomaly-focused', () => {
  for (const token of [
    'camera-label',
    'camera-timecode',
    'rec-dot',
    'camera-thumbnails',
  ]) {
    assert.match(html, new RegExp(`class="[^"]*\\b${token}\\b`), `monitor should include ${token}`);
  }
  assert.doesNotMatch(html, /class="[^"]*\bcctv-noise\b/, 'monitor should not use a noise overlay as fake motion');
  assert.doesNotMatch(html, /class="[^"]*\bscanline\b/, 'monitor should not use scanlines as fake motion');
  assert.doesNotMatch(html, /class="[^"]*\bthermal-ghost\b/, 'scene changes should be baked into the GIF instead of overlay ghosts');
  assert.doesNotMatch(css, /hue-rotate\(/, 'scene motion should not rely on RGB hue shifting');
  assert.doesNotMatch(html, /class="anomaly-reticle"/, 'abstract scanner reticles should not be used');
  assert.doesNotMatch(html, /class="elevator-car"/, 'CSS fake elevator car should not replace the GIF');
});

test('hardware console renders icon-first elevator controls', () => {
  assert.match(html, /class="[^"]*\bhardware-console\b/, 'hardware console section should exist');
  assert.match(html, /class="[^"]*\belevator-keypad\b/, 'elevator keypad container should exist');
  assert.match(js, /ACTION_ICONS/, 'runtime should map action IDs to hardware key icons');
  assert.match(js, /openDoor:\s*'◀▯▶'/, 'open door should have an elevator key icon');
  assert.match(js, /emergencyStop:\s*'STOP'/, 'emergency stop should render as STOP');
  assert.match(js, /button\.className\s*=[\s\S]*'hardware-key'/, 'action buttons should render as hardware keys');
  assert.match(js, /emergency-stop/, 'emergency stop should receive a dedicated class');
  assert.match(css, /\.hardware-key\[data-action="emergencyStop"\][\s\S]*border-color:\s*rgba\(255,77,109,0\.72\)/, 'emergency stop should be visually dominant');
});

test('all CCTV background skins are animated GIF assets', () => {
  for (const asset of [
    'cctv-basement-lift-door-open-lite-loop.gif',
    'cctv-hospital-ward-native-lite-loop.gif',
    'cctv-security-room-native-lite-loop.gif',
    'cctv-factory-native-lite-loop.gif',
    'cctv-subway-platform-native-lite-loop.gif',
    'cctv-hotel-lobby-native-lite-loop.gif',
  ]) {
    const escaped = asset.replace(/[.]/g, '\\.');
    assert.match(`${html}\n${css}\n${js}`, new RegExp(escaped), `${asset} should be wired into preview runtime`);
  }
  assert.match(js, /CCTV_GIF_ASSETS/, 'runtime should know how to switch the primary GIF by skin');
  assert.doesNotMatch(css, /--cctv-feed:\s*url\("[^"]+\.png"\)/, 'CCTV feed variables should not point at static PNG backgrounds');
});

test('scene motion does not depend on noise or RGB texture loops', () => {
  assert.match(css, /--hud-glass-texture:\s*url\("assets\/generated\/texture-hud-glass\.png"\)/);
  assert.match(css, /--control-panel-texture:\s*url\("assets\/generated\/texture-control-panel\.png"\)/);
  assert.doesNotMatch(`${html}\n${css}\n${js}`, /overlay-cctv-noise-loop\.gif/);
  assert.doesNotMatch(`${html}\n${css}\n${js}`, /overlay-signal-tear-loop\.gif/);
  assert.match(css, /\.cctv-gif\s*\{[\s\S]*animation:\s*none/, 'primary native scene GIF should carry the motion itself');
  assert.doesNotMatch(`${html}\n${css}\n${js}`, /-scene-loop\.gif/);
});

test('telemetry uses short chips instead of dashboard cards', () => {
  assert.match(html, /class="[^"]*\bsupport-rail\b/, 'support rail should carry telemetry');
  for (const code of ['F', 'DOOR', 'DIR', 'PAX', 'PWR', 'STB', 'ANOM', 'REV', 'DEC', 'LOCK']) {
    assert.match(js, new RegExp(`textContent\\s*=\\s*'${code}'`), `${code} should be applied as a short telemetry label`);
  }
  assert.match(css, /\.status-list div\[data-priority="critical"\][\s\S]*border-color:\s*rgba\(97,255,190,0\.42\)/, 'critical telemetry should have higher contrast');
  assert.match(css, /\.status-list div\[data-priority="secondary"\][\s\S]*opacity:\s*0\.62/, 'secondary telemetry should be de-emphasized');
  assert.match(css, /\.status-list div::after\s*\{\s*display:\s*none/, 'decorative dashboard circles should be removed');
});

test('handoff is a non-covering OVERRIDE strip', () => {
  assert.match(html, /class="[^"]*\bhandoff-strip\b[^"]*\bstart-overlay\b/, 'handoff strip should reuse start overlay ID without covering the game');
  assert.match(html, /data-role="primary-start"[^>]*>OVERRIDE</, 'start action should be a compact OVERRIDE control');
  assert.doesNotMatch(html, /id="startCopy"/, 'handoff should not include prose instruction copy');
  assert.doesNotMatch(html, /id="startChecklist"/, 'handoff should not include checklist content');
  assert.doesNotMatch(html, /id="startFailureRules"/, 'handoff should not include rule badges');
  assert.match(css, /\.handoff-strip\.start-overlay[\s\S]*position:\s*static/, 'handoff should be in normal layout flow');
  assert.doesNotMatch(css, /\.handoff-strip\.start-overlay[\s\S]*position:\s*fixed/, 'handoff should not use fixed positioning');
});

test('portrait mobile layout keeps CCTV first and controls reachable', () => {
  assert.match(css, /Mobile portrait final pass[\s\S]*@media \(max-width:\s*700px\) and \(orientation:\s*portrait\)/, 'mobile override pass should exist');
  assert.match(css, /html, body \{ height:\s*auto; min-height:\s*100dvh; overflow-x:\s*hidden; overflow-y:\s*auto;/, 'portrait should allow vertical scrolling');
  assert.match(css, /grid-template-areas:\s*"monitor"\s*"actions"\s*"status"\s*"logs"/, 'mobile order should be CCTV, controls, telemetry, logs');
  assert.match(css, /\.actions\s*\{[\s\S]*grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\)/, 'mobile controls should be four-column keycaps');
  assert.match(css, /\.start-overlay[\s\S]*position:\s*static;[\s\S]*justify-content:\s*center/, 'mobile OVERRIDE strip should stay in flow');
});

test('generated visual assets are wired into CSS', () => {
  for (const asset of [
    'cctv-basement-lift-door-open-lite-loop.gif',
    'cctv-hospital-ward-native-lite-loop.gif',
    'cctv-security-room-native-lite-loop.gif',
    'cctv-factory-native-lite-loop.gif',
    'cctv-subway-platform-native-lite-loop.gif',
    'cctv-hotel-lobby-native-lite-loop.gif',
    'texture-control-panel.png',
    'texture-hud-glass.png',
  ]) {
    const haystack = `${html}\n${css}\n${js}`;
    assert.match(haystack, new RegExp(asset.replace(/[.]/g, '\\.')), `${asset} should be referenced`);
  }
});

test('preview server serves GIF assets with the correct media type', () => {
  assert.match(previewServer, /'\.gif':\s*'image\/gif'/, 'animated CCTV GIF should be served as image/gif');
});

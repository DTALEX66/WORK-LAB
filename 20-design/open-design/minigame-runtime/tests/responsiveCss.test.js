import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');

test('mobile layout keeps overlays scrollable and controls reachable', () => {
  assert.match(css, /min-height:\s*100dvh/, 'mobile browsers should use dynamic viewport height');
  assert.match(css, /"monitor"\s+"actions"\s+"status"\s+"logs"/, 'mobile layout should show controls right after monitor');
  assert.match(css, /@media \(max-width:\s*700px\) and \(orientation:\s*portrait\)/, 'Android portrait should have a one-screen compact layout');
  assert.match(css, /html, body \{ height:\s*auto; min-height:\s*100dvh; overflow-x:\s*hidden; overflow-y:\s*auto;/, 'Android portrait should allow page-level scrolling');
  assert.match(css, /\.cctv-monitor[\s\S]*min-height:\s*clamp\(330px,\s*56vh,\s*470px\)/, 'CCTV GIF should keep a stable portrait size');
  assert.match(css, /\.actions\s*\{[\s\S]*grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\)/, 'compact layout should keep four-column controls');
  assert.match(css, /\.monitor-caption[\s\S]*?font-size:\s*0\.68rem/, 'monitor text should be a compact caption on phones');
  assert.match(css, /\.cctv-gif/, 'monitor should render a GIF surveillance layer');
  assert.match(css, /\.start-overlay[\s\S]*position:\s*static/, 'OVERRIDE strip should not cover content');
  assert.match(css, /@media \(max-height:\s*480px\) and \(orientation:\s*landscape\)/, 'phone landscape should have a dedicated compact rule');
});

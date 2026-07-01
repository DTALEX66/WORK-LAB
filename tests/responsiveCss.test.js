import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');

test('mobile layout keeps overlays scrollable and controls reachable', () => {
  assert.match(css, /min-height:\s*100dvh/, 'mobile browsers should use dynamic viewport height');
  assert.match(css, /\.start-overlay,[\s\S]*?\.failure-overlay[\s\S]*?overflow:\s*auto/, 'start/failure overlays should scroll on small screens');
  assert.match(css, /"monitor"\s+"actions"\s+"status"\s+"logs"/, 'mobile layout should show controls right after monitor');
  assert.match(css, /@media \(max-width:\s*700px\) and \(orientation:\s*portrait\)/, 'Android portrait should have a one-screen compact layout');
  assert.match(css, /html, body \{ height:\s*100%; overflow:\s*hidden; \}/, 'Android portrait should prevent page-level scrolling');
  assert.match(css, /grid-template-rows:\s*minmax\(225px, 1\.12fr\) auto auto minmax\(74px, 0\.56fr\)/, 'compact layout should fit monitor/actions/status/logs into one viewport');
  assert.match(css, /\.monitor-caption[\s\S]*?max-height:\s*3\.35em/, 'monitor text should be a compact caption on phones');
  assert.match(css, /\.cctv-stage/, 'monitor should render a CCTV scene layer');
  assert.match(css, /@media \(max-height:\s*480px\) and \(orientation:\s*landscape\)/, 'phone landscape should have a dedicated compact rule');
});

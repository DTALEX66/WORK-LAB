import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');

test('short portrait devices fall back to shell scrolling instead of clipping panels', () => {
  const marker = '/* Mobile portrait final pass: keep CCTV first and keep the start strip reachable. */';
  const finalMobile = css.slice(css.lastIndexOf(marker));

  assert.match(finalMobile, /@media \(max-width:\s*700px\) and \(orientation:\s*portrait\) and \(max-height:\s*620px\)/, 'short portrait devices need an explicit fallback');
  assert.match(finalMobile, /max-height:\s*620px[\s\S]*\.console-shell\s*\{[\s\S]*height:\s*100dvh;[\s\S]*overflow-y:\s*auto/, 'short portrait shell should scroll internally rather than clip content');
  assert.match(finalMobile, /max-height:\s*620px[\s\S]*\.grid\s*\{[\s\S]*height:\s*auto;[\s\S]*grid-template-rows:\s*minmax\(120px,\s*32vh\)\s+auto\s+auto\s+minmax\(44px,\s*12vh\)/, 'short portrait should retain a useful CCTV minimum and compact log row');
  assert.match(finalMobile, /padding-bottom:\s*max\([^;]*env\(safe-area-inset-bottom\)/, 'mobile shell should reserve bottom safe-area space');
});

test('mobile layout keeps overlays scrollable internally and controls reachable in one viewport', () => {
  const marker = '/* Mobile portrait final pass: keep CCTV first and keep the start strip reachable. */';
  const finalMobile = css.slice(css.lastIndexOf(marker));

  assert.match(css, /min-height:\s*100dvh/, 'mobile browsers should use dynamic viewport height');
  assert.match(css, /\.start-overlay,[\s\S]*?\.failure-overlay[\s\S]*?overflow:\s*auto/, 'modal overlays should scroll internally on short screens');
  assert.match(finalMobile, /"monitor"\s*"actions"\s*"status"\s*"logs"/, 'mobile layout should show controls right after monitor');
  assert.match(finalMobile, /html, body \{ height:\s*100%; min-height:\s*100dvh; overflow:\s*hidden;/, 'portrait should prevent page-level scrolling');
  assert.match(finalMobile, /grid-template-rows:\s*minmax\(0,\s*1fr\)\s+auto\s+auto\s+minmax\(58px,\s*0\.28fr\)/, 'compact layout should fit monitor/actions/status/logs into one viewport');
  assert.match(finalMobile, /\.monitor-caption[\s\S]*?max-height:\s*2\.6em/, 'monitor text should be a compact caption on phones');
  assert.match(css, /\.cctv-stage/, 'monitor should render a CCTV scene layer');
  assert.match(css, /@media \(max-height:\s*480px\) and \(orientation:\s*landscape\)/, 'phone landscape should have a dedicated compact rule');
});

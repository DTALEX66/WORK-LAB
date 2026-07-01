import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');

test('mobile layout keeps overlays scrollable and controls reachable', () => {
  assert.match(css, /min-height:\s*100dvh/, 'mobile browsers should use dynamic viewport height');
  assert.match(css, /\.start-overlay,[\s\S]*?\.failure-overlay[\s\S]*?overflow:\s*auto/, 'start/failure overlays should scroll on small screens');
  assert.match(css, /"monitor"\s+"actions"\s+"status"\s+"logs"/, 'mobile layout should show controls right after monitor');
  assert.match(css, /@media \(max-height:\s*480px\) and \(orientation:\s*landscape\)/, 'phone landscape should have a dedicated compact rule');
});

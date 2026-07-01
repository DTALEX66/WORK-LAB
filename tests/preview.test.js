import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');

test('browser preview exposes an explicit start handoff overlay', () => {
  assert.match(html, /id="startOverlay"/, 'preview should include a visible start handoff overlay');
  assert.match(html, /id="startButton"/, 'preview should include a dedicated start button');
  assert.match(html, /id="startFailureRules"/, 'preview should show explicit failure rules');
  assert.match(html, /id="failureMetrics"/, 'failure overlay should expose system metrics for review');
  assert.match(html, /data-testid="start-handoff"/, 'start overlay should be easy to target in browser checks');
});

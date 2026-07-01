import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');

test('browser preview exposes an explicit start handoff overlay', () => {
  assert.match(html, /id="startOverlay"/, 'preview should include a visible start handoff overlay');
  assert.match(html, /id="startButton"/, 'preview should include a dedicated start button');
  assert.match(html, /id="startFailureRules"/, 'preview should show explicit failure rules');
  assert.match(html, /id="failureMetrics"/, 'failure overlay should expose system metrics for review');
  assert.match(html, /id="fakeEndingEyebrow"/, 'fake-ending overlay should expose skin-backed eyebrow');
  assert.match(html, /id="fakeEndingTitle"/, 'fake-ending overlay should expose skin-backed title');
  assert.match(html, /id="monitorSignal"/, 'monitor should expose a visual signal state strip');
  assert.match(html, /id="monitorThreat"/, 'monitor should expose a visual threat badge');
  assert.match(html, /class="cctv-stage"/, 'monitor should include a CCTV visual stage, not just text');
  assert.match(html, /id="monitorCaption"/, 'monitor copy should render as caption so visual layer is preserved');
  assert.match(html, /class="passenger-heat"/, 'monitor should include a passenger heat signature visual');
  assert.match(html, /data-testid="start-handoff"/, 'start overlay should be easy to target in browser checks');
  assert.match(html, /id="postRunSummary"/, 'failure overlay should include a post-run summary for player debrief');
  assert.match(html, /id="openArchiveBtn"/, 'start overlay should include an archive button');
  assert.match(html, /id="archiveOverlay"/, 'archive overlay should be present for cross-session collection');
});

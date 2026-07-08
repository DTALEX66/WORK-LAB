import assert from 'node:assert/strict';
import test from 'node:test';

import { createInitialState } from '../src/state.js';
import { deriveVisualState } from '../src/visualState.js';
import { ANOMALIES } from '../src/events.js';

test('visualState keeps clear state calm with no highlighted action', () => {
  const visual = deriveVisualState(createInitialState());

  assert.deepEqual(visual, {
    tone: 'normal',
    glitch: false,
    shake: false,
    noise: 0.18,
    highlightAction: null,
  });
});

test('visualState maps active anomaly to warning effects and an action hint', () => {
  const visual = deriveVisualState({
    ...createInitialState(),
    anomalyLevel: 2,
    activeAnomaly: 'stop_failure',
  });

  assert.equal(visual.tone, 'warn');
  assert.equal(visual.glitch, true);
  assert.equal(visual.shake, false);
  assert.equal(visual.highlightAction, 'restartSystem');
  assert.ok(visual.noise >= 0.44 && visual.noise <= 0.46);
});

test('visualState escalates high anomaly pressure into critical shake and close-door hint', () => {
  const visual = deriveVisualState({
    ...createInitialState(),
    anomalyLevel: 5,
    activeAnomaly: 'door_refuse',
  });

  assert.equal(visual.tone, 'critical');
  assert.equal(visual.glitch, true);
  assert.equal(visual.shake, true);
  assert.equal(visual.highlightAction, 'closeDoor');
  assert.ok(visual.noise >= 0.86 && visual.noise <= 0.87);
});

test('visualState maps game over to danger failure visuals', () => {
  const visual = deriveVisualState({
    ...createInitialState(),
    anomalyLevel: 6,
    gameOver: true,
    activeAnomaly: null,
  });

  assert.equal(visual.tone, 'danger');
  assert.equal(visual.glitch, true);
  assert.equal(visual.shake, true);
  assert.equal(visual.noise, 1);
  assert.equal(visual.highlightAction, 'restartSystem');
});

test('visualState provides an action hint for every shipped anomaly id', () => {
  for (const anomaly of ANOMALIES) {
    const visual = deriveVisualState({
      ...createInitialState(),
      anomalyLevel: anomaly.severity ?? 2,
      activeAnomaly: anomaly.id,
    });

    assert.ok(visual.highlightAction, `${anomaly.id} should produce a recommended action`);
  }
});

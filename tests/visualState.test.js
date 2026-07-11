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
    cctvState: '00_idle_closed',
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
  assert.equal(visual.cctvState, '08_emergency_stop');
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
  assert.equal(visual.cctvState, '20_threat_high');
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
  assert.equal(visual.cctvState, '20_threat_high');
});

test('visualState maps normal elevator conditions to imported CCTV states', () => {
  assert.equal(deriveVisualState({ ...createInitialState(), door: 'open' }).cctvState, '01_door_open');
  assert.equal(deriveVisualState({ ...createInitialState(), direction: 'up' }).cctvState, '04_moving_up');
  assert.equal(deriveVisualState({ ...createInitialState(), direction: 'down' }).cctvState, '05_moving_down');
  assert.equal(deriveVisualState({ ...createInitialState(), power: 18 }).cctvState, '06_power_low');
  assert.equal(deriveVisualState({ ...createInitialState(), power: 4 }).cctvState, '07_power_outage');
  assert.equal(deriveVisualState({ ...createInitialState(), fakeEndingCooldownRemaining: 1 }).cctvState, '23_cooldown_safe');
  assert.equal(deriveVisualState({ ...createInitialState(), anomalyLevel: 2, activeAnomaly: 'door_refuse' }).cctvState, '09_door_jammed');
});

test('visualState keeps successful settlement calm while highlighting restart', () => {
  const visual = deriveVisualState({
    ...createInitialState(),
    gameOver: true,
    result: 'success',
    remaining: 0,
  });

  assert.equal(visual.tone, 'normal');
  assert.equal(visual.glitch, false);
  assert.equal(visual.shake, false);
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

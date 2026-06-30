import test from 'node:test';
import assert from 'node:assert/strict';

import { createInitialState } from '../src/state.js';
import { ANOMALIES, applyAnomaly, pickNextAnomaly } from '../src/events.js';

test('anomaly catalogue contains at least five playable events', () => {
  assert.ok(ANOMALIES.length >= 5);
  for (const event of ANOMALIES) {
    assert.ok(event.id);
    assert.ok(event.title);
    assert.ok(event.severity >= 1);
    assert.ok(event.adHint);
  }
});

test('applyAnomaly mutates system state and logs the event', () => {
  const state = createInitialState();
  const result = applyAnomaly(state, 'phantom_floor');

  assert.equal(result.state.floor, 13);
  assert.equal(result.state.anomalyLevel, 2);
  assert.match(result.state.logs.at(-1).text, /不存在的楼层/);
});

test('pickNextAnomaly is deterministic when random source is injected', () => {
  const selected = pickNextAnomaly(createInitialState(), () => 0);
  assert.equal(selected.id, ANOMALIES[0].id);
});

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

test('anomaly catalogue contains at least 12 events for good variety', () => {
  assert.ok(ANOMALIES.length >= 12);
  const ids = ANOMALIES.map(e => e.id);
  const unique = new Set(ids);
  assert.equal(unique.size, ANOMALIES.length, 'all anomaly IDs must be unique');
});

test('pickNextAnomaly is deterministic when random source is injected', () => {
  const selected = pickNextAnomaly(createInitialState(), () => 0);
  assert.equal(selected.id, ANOMALIES[0].id);
});

test('new anomalies: door_refuse forces door open', () => {
  const state = createInitialState();
  const result = applyAnomaly(state, 'door_refuse');
  assert.equal(result.state.door, 'open');
  assert.match(result.state.logs.at(-1).text, /门拒绝关闭/);
});

test('new anomalies: floor_jump skips floors', () => {
  const state = { ...createInitialState(), floor: 5 };
  const result = applyAnomaly(state, 'floor_jump');
  assert.ok(result.state.floor > 5, 'floor should increase');
  assert.match(result.state.logs.at(-1).text, /楼层编号跳跃/);
});

test('new anomalies: emergency_lights drains significant power', () => {
  const state = createInitialState();
  const result = applyAnomaly(state, 'emergency_lights');
  assert.ok(result.state.power < 85, 'power should drop sharply');
  assert.ok(result.state.anomalyLevel >= 3);
});

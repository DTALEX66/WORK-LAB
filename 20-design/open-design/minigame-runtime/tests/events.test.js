import test from 'node:test';
import assert from 'node:assert/strict';

import CONFIG from '../src/gameConfig.js';
import { createInitialState } from '../src/state.js';
import { ANOMALIES, applyAnomaly, pickNextAnomaly, HIDDEN_LOGS } from '../src/events.js';
import { loadSkin } from '../src/skinManager.js';
import elevatorSkin from '../src/skins/elevator/skin.json' with { type: 'json' };

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

test('applyAnomaly uses current skin anomaly log copy', () => {
  const skin = structuredClone(elevatorSkin);
  skin.ui.anomalyEventLog = '皮肤异常：{title} / {hint}';
  loadSkin(skin);

  const result = applyAnomaly(createInitialState(), 'phantom_floor');

  assert.match(result.state.logs.at(-1).text, /皮肤异常：不存在的楼层 \/ 当楼层显示 13 时/);

  loadSkin(elevatorSkin);
});

test('anomaly numeric effects add meters but set absolute fields', () => {
  const state = { ...createInitialState(), floor: 1, passengers: 2, anomalyLevel: 2 };

  const floorResult = applyAnomaly(state, 'phantom_floor');
  assert.equal(floorResult.state.floor, 13, 'floor should be set to absolute skin value');
  assert.equal(floorResult.state.anomalyLevel, 4, 'anomaly level should increase by skin value');

  const passengerResult = applyAnomaly(state, 'zero_passenger_shadow');
  assert.equal(passengerResult.state.passengers, 0, 'passengers should be set to absolute skin value');
  assert.equal(passengerResult.state.anomalyLevel, 4, 'anomaly level should increase by skin value');
});

test('anomaly string delta effects clamp meter fields', () => {
  const result = applyAnomaly({ ...createInitialState(), floor: CONFIG.bounds.maxFloor - 1 }, 'floor_jump');

  assert.equal(result.state.floor, CONFIG.bounds.maxFloor, 'string delta floor effects should clamp to playable max floor');
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

test('applyAnomaly adds a locked hidden log to state', () => {
  const state = { ...createInitialState(), hiddenLogs: [], logs: [] };
  const result = applyAnomaly(state, 'phantom_floor');
  assert.equal(result.state.hiddenLogs.length, 1);
  assert.equal(result.state.hiddenLogs[0].id, 'phantom_floor_log');
  assert.equal(result.state.hiddenLogs[0].locked, true);
});

test('applyAnomaly does not duplicate hidden logs', () => {
  const state = { ...createInitialState(), hiddenLogs: [], logs: [] };
  const r1 = applyAnomaly(state, 'phantom_floor');
  const r2 = applyAnomaly(r1.state, 'phantom_floor');
  assert.equal(r2.state.hiddenLogs.length, 1, 'should still be 1');
});

test('all 12 anomalies have a corresponding hidden log entry', () => {
  for (const anomaly of ANOMALIES) {
    assert.ok(HIDDEN_LOGS[anomaly.id], `missing hidden log for ${anomaly.id}`);
  }
});

test('applyAnomaly increments post-run summary tracking counters', () => {
  const state = { ...createInitialState(), hiddenLogs: [], logs: [] };
  const r1 = applyAnomaly(state, 'phantom_floor');   // severity 2
  const r2 = applyAnomaly(r1.state, 'emergency_lights'); // severity 3
  assert.equal(r2.state.anomaliesTriggeredTotal, 2);
  assert.equal(r2.state.maxAnomalySeverity, 3);
});

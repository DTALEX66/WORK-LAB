import test from 'node:test';
import assert from 'node:assert/strict';

import { createInitialState, cloneState, reviveFromAd, saveSnapshot } from '../src/state.js';

test('createInitialState returns the elevator console baseline', () => {
  const state = createInitialState();

  assert.equal(state.floor, 1);
  assert.equal(state.door, 'closed');
  assert.equal(state.moving, false);
  assert.equal(state.direction, 'idle');
  assert.equal(state.power, 100);
  assert.equal(state.stability, 100);
  assert.equal(state.anomalyLevel, 0);
  assert.equal(state.passengers, 1);
  assert.equal(state.gameOver, false);
  assert.equal(state.adRevivesUsed, 0);
  assert.ok(Array.isArray(state.logs));
  assert.ok(Array.isArray(state.snapshots), 'snapshots should be initialized as empty array');
  assert.equal(state.snapshots.length, 0);
});

test('cloneState creates a deep copy suitable for rollback snapshots', () => {
  const state = createInitialState();
  const copy = cloneState(state);
  copy.logs.push({ type: 'test', text: 'mutated' });

  assert.equal(state.logs.length, 1);
  assert.notEqual(copy.logs, state.logs);
});

test('saveSnapshot appends a deep copy without nesting snapshots inside the saved state', () => {
  const state = { ...createInitialState(), floor: 5, power: 80, elapsed: 30, snapshots: [] };
  const next = saveSnapshot(state);

  assert.equal(next.snapshots.length, 1);
  assert.equal(next.snapshots[0].at, 30);
  assert.equal(next.snapshots[0].state.floor, 5);
  assert.equal(next.snapshots[0].state.power, 80);
  assert.equal(next.snapshots[0].state.elapsed, 30);
  // The saved state must NOT include its own snapshots array
  assert.ok(!('snapshots' in next.snapshots[0].state), 'saved snapshot state should not nest snapshots');
});

test('saveSnapshot keeps existing snapshots', () => {
  const first = saveSnapshot({ ...createInitialState(), elapsed: 10, snapshots: [] });
  const second = saveSnapshot({ ...first, floor: 3, elapsed: 20 });

  assert.equal(second.snapshots.length, 2);
  assert.equal(second.snapshots[0].at, 10);
  assert.equal(second.snapshots[1].at, 20);
});

test('reviveFromAd restores from the closest snapshot within 30 seconds of rollback', () => {
  const snap1 = { at: 10, state: { floor: 2, door: 'closed', moving: false, direction: 'idle', power: 90, stability: 95, anomalyLevel: 1, passengers: 1, elapsed: 10, remaining: 50, adRevivesUsed: 0, monitor: 'snap at 10', logs: [] } };
  const snap2 = { at: 30, state: { floor: 4, door: 'closed', moving: false, direction: 'idle', power: 60, stability: 70, anomalyLevel: 3, passengers: 1, elapsed: 30, remaining: 30, adRevivesUsed: 0, monitor: 'snap at 30', logs: [] } };
  const snap3 = { at: 40, state: { floor: 6, door: 'open', moving: true, direction: 'up', power: 40, stability: 50, anomalyLevel: 4, passengers: 2, elapsed: 40, remaining: 20, adRevivesUsed: 0, monitor: 'snap at 40', logs: [] } };

  const failed = {
    ...createInitialState(),
    gameOver: true, power: 5, stability: 10, anomalyLevel: 6, elapsed: 58,
    snapshots: [snap1, snap2, snap3],
  };

  const revived = reviveFromAd(failed);

  // Should roll back to snap at 30 (closest to elapsed - 30 = 28)
  assert.equal(revived.floor, 4, 'floor should be from snap at 30');
  assert.equal(revived.power, 60);
  assert.equal(revived.stability, 70);
  assert.equal(revived.anomalyLevel, 3);
  assert.equal(revived.elapsed, 30);
  assert.equal(revived.gameOver, false);
  assert.equal(revived.door, 'closed');
  assert.equal(revived.adRevivesUsed, 1);
  assert.match(revived.monitor, /回滚/);
  assert.match(revived.logs.at(-1).text, /广告复活/);
});

test('reviveFromAd falls back to initial state when snapshots array is empty', () => {
  const failed = {
    ...createInitialState(),
    gameOver: true, power: 0, stability: 0, anomalyLevel: 6, elapsed: 55,
    snapshots: [],
  };

  const revived = reviveFromAd(failed);

  assert.equal(revived.gameOver, false);
  assert.equal(revived.door, 'closed');
  assert.equal(revived.adRevivesUsed, 1);
  // No snapshots → fall back to initial baseline
  assert.equal(revived.floor, 1);
  assert.equal(revived.power, 100);
});

test('reviveFromAd preserves snapshot history after restore', () => {
  const snap = { at: 20, state: { floor: 3, door: 'closed', moving: false, direction: 'idle', power: 75, stability: 85, anomalyLevel: 2, passengers: 1, elapsed: 20, remaining: 40, adRevivesUsed: 0, monitor: 'ok', logs: [] } };

  const failed = {
    ...createInitialState(),
    gameOver: true, anomalyLevel: 6, elapsed: 48,
    snapshots: [snap],
  };

  const revived = reviveFromAd(failed);
  assert.equal(revived.snapshots.length, 1, 'snapshot history should be preserved');
  assert.equal(revived.snapshots[0].at, 20);
});

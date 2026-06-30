import test from 'node:test';
import assert from 'node:assert/strict';

import { createInitialState, cloneState, reviveFromAd } from '../src/state.js';

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
});

test('cloneState creates a deep copy suitable for rollback snapshots', () => {
  const state = createInitialState();
  const copy = cloneState(state);
  copy.logs.push({ type: 'test', text: 'mutated' });

  assert.equal(state.logs.length, 1);
  assert.notEqual(copy.logs, state.logs);
});

test('reviveFromAd restores playable state after failure and records ad revive', () => {
  const failed = { ...createInitialState(), gameOver: true, power: 0, stability: 0, anomalyLevel: 5, adRevivesUsed: 0 };
  const revived = reviveFromAd(failed);

  assert.equal(revived.gameOver, false);
  assert.equal(revived.power, 45);
  assert.equal(revived.stability, 45);
  assert.equal(revived.anomalyLevel, 2);
  assert.equal(revived.adRevivesUsed, 1);
  assert.match(revived.logs.at(-1).text, /广告复活/);
});

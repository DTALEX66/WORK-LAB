import test from 'node:test';
import assert from 'node:assert/strict';

import { createInitialState } from '../src/state.js';
import { performAction } from '../src/actions.js';

test('elevator cannot move while the door is open', () => {
  const open = performAction(createInitialState(), 'openDoor').state;
  const result = performAction(open, 'moveUp');

  assert.equal(result.ok, false);
  assert.equal(result.state.floor, 1);
  assert.match(result.message, /门未关闭/);
});

test('moveUp consumes power, changes floor, and emits feedback log', () => {
  const result = performAction(createInitialState(), 'moveUp');

  assert.equal(result.ok, true);
  assert.equal(result.state.floor, 2);
  assert.equal(result.state.power, 94);
  assert.equal(result.state.direction, 'up');
  assert.match(result.state.logs.at(-1).text, /上行/);
});

test('restartSystem reduces anomaly level and stabilizes the system', () => {
  const state = { ...createInitialState(), anomalyLevel: 4, stability: 45, power: 55 };
  const result = performAction(state, 'restartSystem');

  assert.equal(result.ok, true);
  assert.equal(result.state.anomalyLevel, 2);
  assert.equal(result.state.stability, 60);
  assert.equal(result.state.power, 45);
});

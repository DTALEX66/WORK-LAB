import test from 'node:test';
import assert from 'node:assert/strict';

import { createInitialState } from '../src/state.js';
import { performAction } from '../src/actions.js';
import CONFIG from '../src/gameConfig.js';

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
  assert.equal(result.state.power, CONFIG.initial.power - CONFIG.actions.moveUp.powerCost);
  assert.equal(result.state.direction, 'up');
  assert.match(result.state.logs.at(-1).text, /上行/);
});

test('restartSystem reduces anomaly level and stabilizes the system', () => {
  const state = { ...createInitialState(), anomalyLevel: 4, stability: 45, power: 55 };
  const result = performAction(state, 'restartSystem');

  assert.equal(result.ok, true);
  assert.equal(result.state.anomalyLevel, 2);
  assert.equal(result.state.stability, 45 + CONFIG.actions.restartSystem.stabilityRestore);
  assert.equal(result.state.power, 55 - CONFIG.actions.restartSystem.powerCost);
});

test('unlockHiddenLog fails when no locked logs exist', () => {
  const result = performAction(createInitialState(), 'unlockHiddenLog');
  assert.equal(result.ok, false);
  assert.match(result.message, /没有待解码/);
});

test('unlockHiddenLog unlocks the first locked hidden log', () => {
  const state = {
    ...createInitialState(),
    hiddenLogs: [
      { id: 'log_a', title: 'Log A', content: 'Content A', locked: true },
      { id: 'log_b', title: 'Log B', content: 'Content B', locked: true },
    ],
  };
  const result = performAction(state, 'unlockHiddenLog');
  assert.equal(result.ok, true);
  assert.equal(result.state.hiddenLogs[0].locked, false);
  assert.equal(result.state.hiddenLogs[1].locked, true);
  assert.equal(result.state.adHintsUsed, 1);
});

test('inspectLog reports locked hidden records when available', () => {
  const state = {
    ...createInitialState(),
    hiddenLogs: [
      { id: 'log_a', title: 'Log A', content: 'Content A', locked: true },
      { id: 'log_b', title: 'Log B', content: 'Content B', locked: false },
      { id: 'log_c', title: 'Log C', content: 'Content C', locked: true },
    ],
  };

  const result = performAction(state, 'inspectLog');

  assert.equal(result.ok, true);
  assert.match(result.state.logs.at(-1).text, /2 条待解码加密记录/);
});

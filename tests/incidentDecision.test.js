import assert from 'node:assert/strict';
import test from 'node:test';

import { createInitialState } from '../src/state.js';
import { expireInspection, openInspection, submitInspection } from '../src/incidentDecision.js';

test('normal baseline must be explicitly classified and rewards a correct decision', () => {
  const opened = openInspection(createInitialState(), {
    id: 'baseline-0',
    kind: 'normal',
    title: '当前监控未见异常',
    duration: 6,
  });
  assert.equal(opened.inspection.status, 'pending');
  assert.equal(opened.inspection.expiresAt, 6);

  const result = submitInspection(opened, 'normal');
  assert.equal(result.accepted, true);
  assert.equal(result.correct, true);
  assert.equal(result.state.inspection.status, 'resolved');
  assert.equal(result.state.decisionsCorrect, 1);
  assert.equal(result.state.decisionsWrong, 0);
});

test('misclassifying an anomaly applies a real gameplay penalty', () => {
  const initial = { ...createInitialState(), elapsed: 12, stability: 80, anomalyLevel: 2 };
  const opened = openInspection(initial, {
    id: 'phantom_floor',
    kind: 'anomaly',
    title: '楼层显示与建筑图纸不一致',
    duration: 7,
  });
  const result = submitInspection(opened, 'normal');
  assert.equal(result.accepted, true);
  assert.equal(result.correct, false);
  assert.equal(result.state.stability, 68);
  assert.equal(result.state.anomalyLevel, 3);
  assert.equal(result.state.decisionsWrong, 1);
});

test('correctly reporting an anomaly reduces pressure but keeps its operational consequence', () => {
  const initial = { ...createInitialState(), anomalyLevel: 3, activeAnomaly: 'phantom_floor' };
  const opened = openInspection(initial, {
    id: 'phantom_floor',
    kind: 'anomaly',
    title: '不存在的楼层',
    duration: 7,
  });
  const result = submitInspection(opened, 'anomaly');
  assert.equal(result.correct, true);
  assert.equal(result.state.anomalyLevel, 2);
  assert.equal(result.state.activeAnomaly, 'phantom_floor');
});

test('inspection timeout cannot overwrite an already successful settlement', () => {
  const state = openInspection(createInitialState(), {
    id: 'last-second', kind: 'normal', title: '最终巡检', duration: 3,
  });
  const settled = { ...state, elapsed: 60, remaining: 0, gameOver: true, result: 'success', stability: 5 };
  const expired = expireInspection(settled);
  assert.equal(expired.timedOut, false);
  assert.equal(expired.state.result, 'success');
  assert.equal(expired.state.stability, 5);
});

test('inspection timeout penalizes exactly once', () => {
  const opened = openInspection({ ...createInitialState(), elapsed: 5 }, {
    id: 'baseline-5',
    kind: 'normal',
    title: '常规巡检',
    duration: 4,
  });
  const expired = expireInspection({ ...opened, elapsed: 9 });
  assert.equal(expired.timedOut, true);
  assert.equal(expired.state.inspection.status, 'expired');
  assert.equal(expired.state.stability, 92);
  const again = expireInspection({ ...expired.state, elapsed: 20 });
  assert.equal(again.timedOut, false);
  assert.equal(again.state.stability, 92);
});

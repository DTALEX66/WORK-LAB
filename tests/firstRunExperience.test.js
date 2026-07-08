import test from 'node:test';
import assert from 'node:assert/strict';

import CONFIG from '../src/gameConfig.js';
import { createInitialState } from '../src/state.js';
import { summarizeFailure } from '../src/feedback.js';
import { getOperatorCue } from '../src/firstRunGuidance.js';

test('first session surfaces an anomaly within the first 10 seconds', () => {
  assert.ok(CONFIG.anomaly.firstTriggerAt <= 10, 'first anomaly should appear quickly enough for a first-session hook');
});

test('operator cue tells new players what to watch before the first anomaly', () => {
  const state = createInitialState();
  const cue = getOperatorCue(state, CONFIG.anomaly.firstTriggerAt, null);

  assert.match(cue, /CCTV/);
  assert.match(cue, /\d+s/);
});

test('operator cue points to the recommended action during the first anomaly', () => {
  const state = {
    ...createInitialState(),
    elapsed: 8,
    activeAnomaly: 'camera_delay',
    anomalyLevel: 1,
    anomaliesTriggeredTotal: 1,
  };

  const cue = getOperatorCue(state, CONFIG.anomaly.firstTriggerAt, '日志');

  assert.match(cue, /日志/);
  assert.match(cue, /黄色/);
});

test('first failure summary teaches revive and the next read target', () => {
  const state = {
    ...createInitialState(),
    elapsed: 12,
    power: 0,
    gameOver: true,
    anomaliesTriggeredTotal: 1,
    adRevivesUsed: 0,
  };

  const summary = summarizeFailure(state);

  assert.match(summary, /广告复活/);
  assert.match(summary, /监控|日志|推荐按键/);
});

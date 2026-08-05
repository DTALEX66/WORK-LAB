import test from 'node:test';
import assert from 'node:assert/strict';

import {
  ANALYTICS_EVENTS,
  createConsoleAnalyticsSink,
  resetAnalyticsSink,
  setAnalyticsSink,
  trackEvent,
} from '../src/analytics.js';

test('analytics exposes the minigame monetization and gameplay event surface', () => {
  assert.deepEqual(ANALYTICS_EVENTS, Object.freeze([
    'game_start',
    'game_over',
    'revive_ad_start',
    'revive_ad_reward',
    'hidden_log_ad_start',
    'hidden_log_unlock',
    'fake_ending_trigger',
    'action_click',
    'anomaly_trigger',
  ]));
});

test('trackEvent sends normalized payloads to the injected sink', () => {
  const calls = [];
  setAnalyticsSink((event) => calls.push(event));

  try {
    const result = trackEvent('action_click', {
      actionId: 'openDoor',
      skinId: 'subway',
      elapsed: 12,
    }, {
      now: () => 12345,
    });

    assert.deepEqual(result, {
      name: 'action_click',
      ts: 12345,
      skinId: 'subway',
      elapsed: 12,
      actionId: 'openDoor',
    });
    assert.deepEqual(calls, [result]);
  } finally {
    resetAnalyticsSink();
  }
});

test('trackEvent rejects unknown analytics events', () => {
  assert.throws(() => trackEvent('unknown_event'), /Unknown analytics event/);
});

test('console analytics sink logs a stable prefix and event payload', () => {
  const calls = [];
  const sink = createConsoleAnalyticsSink({
    log: (...args) => calls.push(args),
  });

  sink({ name: 'game_start', ts: 1, skinId: 'elevator' });

  assert.deepEqual(calls, [[
    '[analytics]',
    'game_start',
    { name: 'game_start', ts: 1, skinId: 'elevator' },
  ]]);
});

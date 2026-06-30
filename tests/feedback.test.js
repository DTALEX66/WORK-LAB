import test from 'node:test';
import assert from 'node:assert/strict';

import { createInitialState } from '../src/state.js';
import { createFeedbackLine, summarizeFailure } from '../src/feedback.js';

test('createFeedbackLine formats timestamped console feedback', () => {
  const line = createFeedbackLine('warn', '门外检测到人影', 42);

  assert.deepEqual(line, {
    type: 'warn',
    time: 42,
    text: '[00:42] 门外检测到人影',
  });
});

test('summarizeFailure explains why the run ended', () => {
  const state = { ...createInitialState(), power: 0, stability: 12, anomalyLevel: 4 };
  const summary = summarizeFailure(state);

  assert.match(summary, /电源耗尽/);
  assert.match(summary, /观看广告/);
});

import test from 'node:test';
import assert from 'node:assert/strict';

import CONFIG from '../src/gameConfig.js';
import { createRuntimeSession, restartRuntimeSession } from '../src/runtimeSession.js';

test('runtime session uses configured first anomaly time on start and restart', () => {
  const session = createRuntimeSession();
  assert.equal(session.nextAnomalyAt, CONFIG.anomaly.firstTriggerAt);

  const restarted = restartRuntimeSession({ ...session, nextAnomalyAt: 999 });
  assert.equal(restarted.nextAnomalyAt, CONFIG.anomaly.firstTriggerAt);
  assert.equal(restarted.state.elapsed, 0);
});

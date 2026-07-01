import test from 'node:test';
import assert from 'node:assert/strict';

import { loadSkin } from '../src/skinManager.js';
import securitySkin from '../src/skins/security/skin.json' with { type: 'json' };
import elevatorSkin from '../src/skins/elevator/skin.json' with { type: 'json' };
import { getDomLabels } from '../src/uiLabels.js';

test('DOM labels use current skin labels', () => {
  loadSkin(securitySkin);
  const labels = getDomLabels();

  assert.equal(labels.statusPanel, '安防状态');
  assert.equal(labels.status.floor, '区域');
  assert.equal(labels.status.door, '门禁');
  assert.equal(labels.status.passengers, '人员');
  assert.equal(labels.monitorPanel, '安防监控');
  assert.equal(labels.actionPanel, '安防操作');
  assert.equal(labels.logPanel, '安防日志');
  assert.equal(labels.forceAnomaly, '触发安防异常');
  assert.equal(labels.failureTitle, '安防系统崩溃');

  loadSkin(elevatorSkin);
});

import test from 'node:test';
import assert from 'node:assert/strict';

import { createInitialState } from '../src/state.js';
import { loadSkin } from '../src/skinManager.js';
import securitySkin from '../src/skins/security/skin.json' with { type: 'json' };
import elevatorSkin from '../src/skins/elevator/skin.json' with { type: 'json' };
import { getCanvasActionButtons, getCanvasStaticLabels, getCanvasStatusItems } from '../platform/canvasRenderer.js';

test('canvas action buttons use current skin labels', () => {
  loadSkin(securitySkin);
  const labels = getCanvasActionButtons(createInitialState()).map(button => button.label);

  assert.ok(labels.includes('解锁门禁'));
  assert.ok(labels.includes('锁定门禁'));
  assert.ok(labels.includes('查看安防日志'));
  assert.ok(!labels.includes('开门'));

  loadSkin(elevatorSkin);
});

test('canvas action buttons show locked hidden-log count', () => {
  loadSkin(elevatorSkin);
  const state = {
    ...createInitialState(),
    hiddenLogs: [
      { id: 'a', title: 'A', content: 'A', locked: true },
      { id: 'b', title: 'B', content: 'B', locked: true },
    ],
  };

  const labels = getCanvasActionButtons(state).map(button => button.label);

  assert.ok(labels.includes('解码加密记录 (2)'));
});

test('canvas status items use current skin status labels', () => {
  loadSkin(securitySkin);
  const labels = getCanvasStatusItems(createInitialState()).map(item => item.label);

  assert.ok(labels.includes('区域'));
  assert.ok(labels.includes('门禁'));
  assert.ok(labels.includes('人员'));
  assert.ok(!labels.includes('楼层'));

  loadSkin(elevatorSkin);
});

test('canvas static labels use current skin copy', () => {
  loadSkin(securitySkin);
  const labels = getCanvasStaticLabels();

  assert.equal(labels.countdown, '值守倒计时');
  assert.equal(labels.monitorPanel, '安防监控');
  assert.equal(labels.actionPanel, '安防操作');
  assert.equal(labels.logPanel, '安防日志');
  assert.equal(labels.forceAnomaly, '触发安防异常');
  assert.equal(labels.failureTitle, '安防系统崩溃');

  loadSkin(elevatorSkin);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { getAvailableActions } from '../src/actions.js';
import { createInitialState } from '../src/state.js';
import { loadSkin } from '../src/skinManager.js';
import securitySkin from '../src/skins/security/skin.json' with { type: 'json' };
import elevatorSkin from '../src/skins/elevator/skin.json' with { type: 'json' };
import { getCanvasActionButtons, getCanvasFailureOverlayCopy, getCanvasMeterBars, getCanvasStaticLabels, getCanvasStatusItems } from '../platform/canvasRenderer.js';
import { getDomLabels } from '../src/uiLabels.js';

const canvasRendererSource = readFileSync(new URL('../platform/canvasRenderer.js', import.meta.url), 'utf8');

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

test('canvas action buttons use the shared action list', () => {
  loadSkin(elevatorSkin);
  const buttons = getCanvasActionButtons(createInitialState());
  const expectedIds = getAvailableActions()
    .map(action => action.id)
    .filter(id => id !== 'unlockHiddenLog');

  assert.deepEqual(buttons.map(button => button.id), expectedIds);
});

test('canvas status items use current skin status labels', () => {
  loadSkin(securitySkin);
  const labels = getCanvasStatusItems(createInitialState()).map(item => item.label);
  const domLabels = getDomLabels();

  assert.ok(labels.includes('区域'));
  assert.ok(labels.includes('门禁'));
  assert.ok(labels.includes('人员'));
  assert.ok(!labels.includes('楼层'));
  assert.deepEqual(labels, Object.values(domLabels.status));

  loadSkin(elevatorSkin);
});

test('canvas meter bars use current skin status labels', () => {
  loadSkin(securitySkin);
  const bars = getCanvasMeterBars({ ...createInitialState(), power: 42, stability: 77 });

  assert.deepEqual(bars.map(bar => bar.label), ['电力', '安保等级']);
  assert.deepEqual(bars.map(bar => bar.value), [42, 77]);

  loadSkin(elevatorSkin);
});

test('canvas static labels use current skin copy', () => {
  loadSkin(securitySkin);
  const labels = getCanvasStaticLabels();
  const domLabels = getDomLabels();

  assert.equal(labels.countdown, '值守倒计时');
  assert.equal(labels.monitorPanel, '安防监控');
  assert.equal(labels.actionPanel, '安防操作');
  assert.equal(labels.logPanel, '安防日志');
  assert.equal(labels.forceAnomaly, '触发安防异常');
  assert.equal(labels.failureTitle, '安防系统崩溃');
  assert.equal(labels.failureEyebrow, 'SECURITY FAILURE');
  assert.equal(labels.countdown, domLabels.countdown);
  assert.equal(labels.monitorPanel, domLabels.monitorPanel);
  assert.equal(labels.actionPanel, domLabels.actionPanel);
  assert.equal(labels.logPanel, domLabels.logPanel);
  assert.equal(labels.forceAnomaly, domLabels.forceAnomaly);
  assert.equal(labels.failureTitle, domLabels.failureTitle);
  assert.equal(labels.failureEyebrow, domLabels.failureEyebrow);
  assert.equal(labels.adRevive, domLabels.revive);
  assert.equal(labels.restart, domLabels.restart);
  assert.equal(labels.revealTruth, domLabels.revealTruth);

  loadSkin(elevatorSkin);
});

test('canvas failure overlay copy uses current skin text', () => {
  const skin = structuredClone(securitySkin);
  skin.canvasLabels.failureEyebrow = 'SECURITY FAILURE';
  loadSkin(skin);

  const fakeEndingCopy = getCanvasFailureOverlayCopy({
    ...createInitialState(),
    gameOver: true,
    fakeEndingTriggered: true,
  });
  assert.equal(fakeEndingCopy.eyebrow, '⚠ SYSTEM ANOMALY DETECTED');
  assert.equal(fakeEndingCopy.title, '值班员关联异常');

  const failureCopy = getCanvasFailureOverlayCopy({
    ...createInitialState(),
    gameOver: true,
    lastAdHint: '先锁门。',
  });
  assert.equal(failureCopy.eyebrow, 'SECURITY FAILURE');
  assert.equal(failureCopy.adHintLine, '系统提示：先锁门。');

  loadSkin(elevatorSkin);
});

test('canvas monitor renderer draws a visual CCTV scene before caption text', () => {
  assert.match(canvasRendererSource, /function drawCctvScene/, 'Canvas mini-game monitor should include visual CCTV scene rendering');
  assert.match(canvasRendererSource, /drawCctvScene\(state/, 'drawMonitor should call the visual scene renderer');
  assert.match(canvasRendererSource, /heatAlpha/, 'Canvas monitor should draw passenger heat signature state');
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { getAvailableActions } from '../src/actions.js';
import { createInitialState } from '../src/state.js';
import { loadSkin } from '../src/skinManager.js';
import securitySkin from '../src/skins/security/skin.json' with { type: 'json' };
import elevatorSkin from '../src/skins/elevator/skin.json' with { type: 'json' };
import { getCanvasActionButtons, getCanvasCctvTreatment, getCanvasFailureOverlayCopy, getCanvasLayout, getCanvasMeterBars, getCanvasMuteControl, getCanvasStaticLabels, getCanvasStatusItems, getCanvasVisibleActionButtons, getCanvasVisibleLogs, onCanvasClick } from '../platform/canvasRenderer.js';
import { getDomLabels } from '../src/uiLabels.js';

const canvasRendererSource = readFileSync(new URL('../platform/canvasRenderer.js', import.meta.url), 'utf8');

test('Canvas V4 uses one dominant CCTV, three large readings and a two-button thumb zone', () => {
  const layout = getCanvasLayout(1334);
  const cssScale = 393 / 750;
  assert.ok(layout.monitor.w > 700 && layout.monitor.h >= 520);
  assert.ok(layout.readings.y > layout.monitor.y + layout.monitor.h);
  assert.ok(layout.actions.y > layout.readings.y + layout.readings.h);
  assert.equal(layout.actions.columns, 2);
  assert.ok(layout.actions.buttonH * cssScale >= 48);
  assert.ok(layout.actions.buttonH * (360 / 750) >= 48, 'short 360px phones keep full-size thumb targets');
  assert.ok(layout.feedback.y > layout.actions.y + layout.actions.h);
  assert.ok(layout.feedback.y + layout.feedback.h <= 1334, '360x640 design-height viewport must not clip feedback');
  assert.equal(layout.logs, undefined);
  assert.equal(layout.status, undefined);
});

test('Canvas mute control remains reachable before and during play', () => {
  const state = createInitialState();
  const preStartControl = getCanvasMuteControl(1334, 0, false);
  const playingControl = getCanvasMuteControl(1334, 0, true);
  const cssScale = 390 / 750;
  assert.ok(preStartControl.h * cssScale >= 44);
  assert.ok(playingControl.h * cssScale >= 44);
  let toggles = 0;
  onCanvasClick(
    preStartControl.x + preStartControl.w / 2,
    preStartControl.y + preStartControl.h / 2,
    state,
    { onToggleMute: () => { toggles += 1; } },
    { started: false, muted: false },
  );
  onCanvasClick(
    playingControl.x + playingControl.w / 2,
    playingControl.y + playingControl.h / 2,
    state,
    { onToggleMute: () => { toggles += 1; } },
    { started: true, muted: false },
  );
  assert.equal(toggles, 2);
});

test('Canvas V4 removes the four-key deck and exposes only the current two-choice task', () => {
  loadSkin(elevatorSkin);
  const idle = getCanvasVisibleActionButtons(createInitialState());
  assert.equal(idle.length, 1);
  assert.equal(idle[0].disabled, true);

  const anomaly = {
    ...createInitialState(),
    activeAnomaly: 'phantom_floor',
    inspection: { id: 'phantom_floor', kind: 'anomaly', status: 'resolved' },
  };
  const treatment = getCanvasVisibleActionButtons(anomaly);
  assert.equal(treatment.length, 1);
  assert.equal(treatment[0].id, 'autoTreatment');
  assert.equal(treatment[0].disabled, true);
  assert.equal(treatment.some(button => button.recommended), false);
});

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

test('pending inspection promotes normal/anomaly decisions to the first two controls', () => {
  loadSkin(elevatorSkin);
  const state = {
    ...createInitialState(),
    inspection: { id: 'baseline', kind: 'normal', title: '当前画面', status: 'pending', expiresAt: 6 },
  };
  const buttons = getCanvasActionButtons(state);
  assert.deepEqual(buttons.slice(0, 2).map(button => button.id), ['reportNormal', 'reportAnomaly']);
  assert.deepEqual(buttons.slice(0, 2).map(button => button.label), ['放行', '封锁']);
});

test('pending anomaly hides answer-giving logs and operational highlights until classified', () => {
  loadSkin(elevatorSkin);
  const state = {
    ...createInitialState(),
    activeAnomaly: { id: 'mirror_mismatch' },
    elapsed: 8,
    inspection: { id: 'mirror_mismatch', kind: 'anomaly', status: 'pending', openedAt: 8, expiresAt: 15 },
    logs: [
      { time: 2, type: 'info', text: '旧日志' },
      { time: 8, type: 'warn', text: '异常答案与操作提示' },
    ],
  };
  assert.deepEqual(getCanvasVisibleLogs(state).map(log => log.text), ['旧日志']);
  assert.equal(getCanvasActionButtons(state).slice(2).some(button => button.recommended), false);
  assert.equal(getCanvasActionButtons(state).slice(2).every(button => button.disabled), true);

  const resolved = { ...state, inspection: { ...state.inspection, status: 'resolved' } };
  assert.equal(getCanvasVisibleLogs(resolved).at(-1).text, '异常答案与操作提示');
});

test('inspection controls dispatch semantic decisions instead of maintenance actions', () => {
  loadSkin(elevatorSkin);
  const state = {
    ...createInitialState(),
    inspection: { id: 'anomaly', kind: 'anomaly', title: '异常', status: 'pending', expiresAt: 7 },
  };
  const layout = getCanvasLayout(1334).actions;
  let decision = null;
  let action = null;
  const x = layout.x + 16 + layout.buttonW / 2;
  const y = layout.startY + layout.buttonH / 2;
  onCanvasClick(x, y, state, {
    onDecision: value => { decision = value; },
    onAction: value => { action = value; },
  });
  assert.equal(decision, 'normal');
  assert.equal(action, null);

  const operationX = layout.x + 16 + 2 * (layout.buttonW + layout.gap) + layout.buttonW / 2;
  onCanvasClick(operationX, y, state, {
    onDecision: value => { decision = value; },
    onAction: value => { action = value; },
  });
  assert.equal(action, null, 'operations stay disabled until the inspection is classified');
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
  assert.equal(labels.forceAnomaly, undefined, 'Canvas bundle must not expose the browser debug trigger');
  assert.equal(labels.failureTitle, '安防系统崩溃');
  assert.equal(labels.failureEyebrow, 'SECURITY FAILURE');
  assert.equal(labels.countdown, domLabels.countdown);
  assert.equal(labels.monitorPanel, domLabels.monitorPanel);
  assert.equal(labels.actionPanel, domLabels.actionPanel);
  assert.equal(labels.logPanel, domLabels.logPanel);
  assert.notEqual(labels.forceAnomaly, domLabels.forceAnomaly);
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

test('canvas renderer distinguishes success settlement from failure', () => {
  assert.match(canvasRendererSource, /state\.result === 'success'/, 'Canvas overlay should branch on explicit success result');
  assert.match(canvasRendererSource, /if \(!isSuccess\)[\s\S]*labels\.adRevive/, 'Canvas success settlement should omit rewarded-revive CTA');
});

test('canvas CCTV treatment consumes the shared cctvState mapping', () => {
  assert.deepEqual(getCanvasCctvTreatment('00_idle_closed'), {
    tint: 'rgba(97,255,190,0.05)', darkness: 0, entity: false, glitch: false, threat: false,
  });
  assert.equal(getCanvasCctvTreatment('13_entity_near').entity, true);
  assert.equal(getCanvasCctvTreatment('20_threat_high').threat, true);
  assert.equal(getCanvasCctvTreatment('10_signal_lost').glitch, true);
  assert.match(canvasRendererSource, /const cctvState = motion\?\.cctvState \|\| baseVisual\.cctvState/, 'Canvas scene should prefer the live motion timeline and fall back to deriveVisualState');
  assert.match(canvasRendererSource, /getCanvasCctvTreatment\(cctvState\)/);
});

test('canvas CCTV effects consume the pausable motion frame clock', () => {
  assert.match(canvasRendererSource, /const frameTime = Number\(motion\?\.frameTime/);
  assert.match(canvasRendererSource, /drawCanvasAnomalyArtifacts\(visual, x, y, w, h, frameTime\)/);
  assert.doesNotMatch(canvasRendererSource, /Math\.sin\(Date\.now\(\)/);
  assert.doesNotMatch(canvasRendererSource, /tearY[\s\S]{0,80}Date\.now\(\)/);
});

test('canvas monitor masks baked CCTV answers and replaces them with neutral runtime clues', () => {
  assert.match(canvasRendererSource, /状态图含固定英文诊断与固定楼层/);
  assert.match(canvasRendererSource, /\['phantom_floor', 'floor_jump', 'negative_floor'\]/);
  assert.match(canvasRendererSource, /源图已裁掉烘焙答案区/);
  assert.match(canvasRendererSource, /始终显示实际楼层/);
  assert.match(canvasRendererSource, /画面楼层/);
  assert.doesNotMatch(canvasRendererSource, /CABIN FEED|SIGNAL VARIANCE|ANOMALY CONFIRMED/);
  assert.doesNotMatch(canvasRendererSource, /fillText\(['"]FLOOR MISMATCH/);
});

test('Canvas V4 render path removes dashboard clutter and keeps gameplay type readable', () => {
  const renderBlock = canvasRendererSource.match(/export function render[\s\S]*?\n}/)?.[0] || '';
  assert.doesNotMatch(renderBlock, /drawStatusPanel/);
  assert.doesNotMatch(renderBlock, /drawLogs/);
  assert.match(renderBlock, /drawRuleStrip/);
  assert.match(renderBlock, /drawReadings/);
  assert.match(canvasRendererSource, /bold 34px [^\n]*Microsoft YaHei/);
  assert.match(canvasRendererSource, /font = '26px [^\n]*Microsoft YaHei/);
});

test('canvas monitor renderer draws a visual CCTV scene before caption text', () => {
  assert.match(canvasRendererSource, /function drawCctvScene/, 'Canvas mini-game monitor should include visual CCTV scene rendering');
  assert.match(canvasRendererSource, /drawCctvScene\(state/, 'drawMonitor should call the visual scene renderer');
  assert.match(canvasRendererSource, /heatAlpha/, 'Canvas monitor should draw passenger heat signature state');
});

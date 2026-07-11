/**
 * canvasRenderer.js — Canvas 渲染器
 *
 * 完全替代 index.html + styles.css 的 DOM 渲染。
 * 在小游戏平台（微信/抖音）上使用 Canvas 渲染，
 * 在浏览器中也可作为独立渲染模式。
 *
 * 设计宽度：750px（标准移动端设计尺寸）
 */

import { getAvailableActions } from '../src/actions.js';
import { t, getSkin, actionLabel } from '../src/skinManager.js';
import { summarizeFailure } from '../src/feedback.js';
import { getDecodedMonitorText, getDirectionLabel, getDomLabels, getDoorLabel } from '../src/uiLabels.js';
import { deriveVisualState } from '../src/visualState.js';

// ── 尺寸常量 ──
const DW = 750;       // 设计宽度
let canvas, ctx;
let scale = 1;        // 实际像素/设计像素比例
let DH = 1334;        // 设计高度（自适应）

// ── 颜色 ──
const COLORS = {
  bg: '#07090a',
  panel: '#101314',
  panelRaised: '#1a1f20',
  line: 'rgba(195,200,190,0.24)',
  text: '#e7e2d5',
  muted: '#8e928c',
  green: '#79d6a3',
  amber: '#e1a84b',
  red: '#e75c4f',
  cyan: '#84b9b0',
  darkRed: '#a52e38',
};

export function getCanvasLayout(height = 1334) {
  const monitor = { x: 14, y: 82, w: 722, h: 510 };
  const actions = {
    x: 14, y: 600, w: 722, h: 238,
    columns: 4, gap: 10, buttonH: 88, startY: 638,
  };
  actions.buttonW = (actions.w - 32 - (actions.columns - 1) * actions.gap) / actions.columns;
  return {
    topbar: { x: 14, y: 12, w: 722, h: 62 },
    monitor,
    actions,
    status: { x: 14, y: 846, w: 722, h: 198 },
    logs: { x: 14, y: 1052, w: 722, h: Math.max(180, height - 1066) },
  };
}

// ── Measure text ──
function measure(text, size, bold = false) {
  ctx.font = `${bold ? 'bold ' : ''}${size}px "Microsoft YaHei", sans-serif`;
  return ctx.measureText(text).width;
}

// ── Draw rounded rect ──
function roundRect(x, y, w, h, r, fill, stroke) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.arcTo(x + w, y, x + w, y + r, r);
  ctx.lineTo(x + w, y + h - r);
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
  ctx.lineTo(x + r, y + h);
  ctx.arcTo(x, y + h, x, y + h - r, r);
  ctx.lineTo(x, y + r);
  ctx.arcTo(x, y, x + r, y, r);
  ctx.closePath();
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = 1; ctx.stroke(); }
}

// ── 绘制背景 ──
function drawBackground() {
  ctx.fillStyle = COLORS.bg;
  ctx.fillRect(0, 0, DW, DH);
  ctx.strokeStyle = 'rgba(255,255,255,0.018)';
  ctx.lineWidth = 1;
  for (let y = 0; y < DH; y += 24) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(DW, y);
    ctx.stroke();
  }
  const glow = ctx.createRadialGradient(DW / 2, 0, 0, DW / 2, 0, 520);
  glow.addColorStop(0, 'rgba(225,168,75,0.06)');
  glow.addColorStop(1, 'transparent');
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, DW, DH);
}

export function getCanvasStaticLabels() {
  const labels = getDomLabels();
  return {
    countdown: labels.countdown,
    monitorPanel: labels.monitorPanel,
    actionPanel: labels.actionPanel,
    logPanel: labels.logPanel,
    forceAnomaly: labels.forceAnomaly,
    failureTitle: labels.failureTitle,
    failureEyebrow: labels.failureEyebrow,
    adRevive: labels.revive,
    restart: labels.restart,
    revealTruth: labels.revealTruth,
  };
}

export function getCanvasFailureOverlayCopy(state) {
  return {
    eyebrow: state.fakeEndingTriggered ? t('fakeEnding.eyebrow') : getCanvasStaticLabels().failureEyebrow,
    title: state.fakeEndingTriggered ? t('fakeEnding.title') : getCanvasStaticLabels().failureTitle,
    adHintLine: state.lastAdHint ? t('failure.adHintPrefix', { hint: state.lastAdHint }) : '',
  };
}

// ── 绘制顶栏 ──
function drawTopbar(state) {
  const { x, y, w, h } = getCanvasLayout(DH).topbar;
  const meta = getSkin().meta;
  roundRect(x, y, w, h, 6, COLORS.panel, COLORS.line);
  ctx.fillStyle = COLORS.green;
  ctx.fillRect(x, y, 5, h);

  ctx.fillStyle = COLORS.text;
  ctx.font = 'bold 28px "Microsoft YaHei", sans-serif';
  ctx.fillText(meta?.name || '', x + 18, y + 37);
  ctx.fillStyle = COLORS.muted;
  ctx.font = '11px Consolas, "Microsoft YaHei", monospace';
  ctx.fillText(meta?.subtitle || '', x + 19, y + 53);

  const cardW = 116;
  const cardX = x + w - cardW - 10;
  roundRect(cardX, y + 9, cardW, h - 18, 4, '#080a0a', 'rgba(225,168,75,0.48)');
  ctx.fillStyle = COLORS.amber;
  ctx.font = 'bold 30px Consolas, monospace';
  ctx.textAlign = 'center';
  ctx.fillText(Math.ceil(state.remaining).toString(), cardX + cardW / 2, y + 42);
  ctx.textAlign = 'left';
}

export function getCanvasStatusItems(state) {
  const labels = getDomLabels().status;

  return [
    { id: 'floor', label: labels.floor, value: state.floor },
    { id: 'door', label: labels.door, value: getDoorLabel(state.door) },
    { id: 'direction', label: labels.direction, value: getDirectionLabel(state.direction) },
    { id: 'passengers', label: labels.passengers, value: state.passengers },
    { id: 'power', label: labels.power, value: `${Math.round(state.power)}%` },
    { id: 'stability', label: labels.stability, value: `${Math.round(state.stability)}%` },
    { id: 'anomalyLevel', label: labels.anomalyLevel, value: state.anomalyLevel },
    { id: 'reviveCount', label: labels.reviveCount, value: state.adRevivesUsed },
    { id: 'adHintsCount', label: labels.adHintsCount, value: state.adHintsUsed },
    { id: 'hiddenLogsCount', label: labels.hiddenLogsCount, value: state.hiddenLogs.filter(h => h.locked).length },
  ];
}

export function getCanvasMeterBars(state) {
  const labels = getDomLabels().status;
  return [
    { id: 'power', label: labels.power, value: state.power, color: COLORS.cyan },
    { id: 'stability', label: labels.stability, value: state.stability, color: COLORS.green },
  ];
}

function getCanvasStatusPanelTitle() {
  return getDomLabels().statusPanel;
}

// ── 绘制状态面板 ──
function drawStatusPanel(state) {
  const { x, y, w, h } = getCanvasLayout(DH).status;
  roundRect(x, y, w, h, 6, COLORS.panel, toneBorder(state));
  ctx.fillStyle = '#bbb9af';
  ctx.font = 'bold 12px Consolas, "Microsoft YaHei", monospace';
  ctx.fillText(`■ ${getCanvasStatusPanelTitle()}`, x + 14, y + 24);

  const coreIds = new Set(['floor', 'door', 'direction', 'passengers', 'power', 'stability', 'anomalyLevel']);
  const items = getCanvasStatusItems(state).filter(item => coreIds.has(item.id));
  const columns = 4;
  const gap = 8;
  const cardW = (w - 32 - gap * (columns - 1)) / columns;
  items.forEach(({ id, label, value }, i) => {
    const cx = x + 16 + (i % columns) * (cardW + gap);
    const cy = y + 36 + Math.floor(i / columns) * 54;
    const stroke = id === 'anomalyLevel' ? 'rgba(231,92,79,0.58)' : 'rgba(121,214,163,0.28)';
    roundRect(cx, cy, cardW, 46, 3, '#090b0c', stroke);
    ctx.fillStyle = COLORS.muted;
    ctx.font = '10px "Microsoft YaHei", sans-serif';
    ctx.fillText(label, cx + 8, cy + 15);
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 17px Consolas, "Microsoft YaHei", monospace';
    ctx.textAlign = 'right';
    ctx.fillText(String(value), cx + cardW - 8, cy + 35);
    ctx.textAlign = 'left';
  });

  getCanvasMeterBars(state).forEach(({ label, value, color }, index) => {
    drawBar(x + 16, y + 148 + index * 20, w - 32, 14, label, value, color);
  });
}

function drawBar(x, y, w, h, label, value, color) {
  ctx.fillStyle = COLORS.muted;
  ctx.font = '11px "Microsoft YaHei", sans-serif';
  ctx.fillText(label, x, y + 12);

  const bx = x + 60, bw = w - 60;
  roundRect(bx, y, bw, h, 6, 'rgba(255,255,255,0.06)');
  const fillW = Math.max(0, (bw - 4) * (value / 100));
  roundRect(bx + 2, y + 2, fillW, h - 4, 4, color);

  ctx.fillStyle = COLORS.text;
  ctx.font = 'bold 11px "Microsoft YaHei", sans-serif';
  ctx.textAlign = 'right';
  ctx.fillText(`${Math.round(value)}`, bx + bw - 4, y + 12);
  ctx.textAlign = 'left';
}

function toneBorder(state) {
  const tone = deriveVisualState(state).tone;
  if (tone === 'danger') return 'rgba(255,77,109,0.55)';
  if (tone === 'critical') return 'rgba(255,209,102,0.38)';
  if (tone === 'warn') return 'rgba(255,209,102,0.38)';
  return COLORS.line;
}

// ── 绘制监控画面 ──
function drawMonitor(state) {
  const { x, y, w, h } = getCanvasLayout(DH).monitor;
  const labels = getCanvasStaticLabels();
  roundRect(x, y, w, h, 6, COLORS.panel, toneBorder(state));
  ctx.fillStyle = '#bbb9af';
  ctx.font = 'bold 12px Consolas, "Microsoft YaHei", monospace';
  ctx.fillText(`■ ${labels.monitorPanel}`, x + 14, y + 24);

  const mx = x + 14, my = y + 34, mw = w - 28, mh = h - 48;
  roundRect(mx, my, mw, mh, 3, '#050807', 'rgba(121,214,163,0.22)');
  drawCctvScene(state, mx + 8, my + 8, mw - 16, mh - 52);

  const scanY = (Date.now() / 100 * (mh - 52)) % (mh - 52);
  ctx.fillStyle = 'rgba(121,214,163,0.04)';
  ctx.fillRect(mx + 8, my + 8 + scanY, mw - 16, 4);

  const displayText = getMonitorText(state);
  ctx.fillStyle = '#c8c6bd';
  ctx.font = '13px "Microsoft YaHei", sans-serif';
  ctx.textAlign = 'center';
  wrapText(displayText, mx + mw / 2, my + mh - 28, mw - 28, 17);
  ctx.textAlign = 'left';
}

export function getCanvasCctvTreatment(cctvState = '00_idle_closed') {
  const glitch = ['10_signal_lost', '11_camera_glitch', '17_loop_corridor'].includes(cctvState);
  const entity = ['13_entity_near', '14_shadow_inside', '15_anomaly_wandering'].includes(cctvState);
  const threat = ['08_emergency_stop', '09_door_jammed', '16_wrong_floor', '20_threat_high'].includes(cctvState);
  const darkness = cctvState === '07_power_outage' ? 0.62 : cctvState === '10_signal_lost' ? 0.38 : 0;
  const tint = threat
    ? 'rgba(255,77,109,0.16)'
    : cctvState === '19_stabilized' || cctvState === '23_cooldown_safe'
      ? 'rgba(97,255,190,0.12)'
      : 'rgba(97,255,190,0.05)';
  return { tint, darkness, entity, glitch, threat };
}

function drawCctvScene(state, x, y, w, h) {
  if (h <= 20) return;
  const visual = deriveVisualState(state);
  const treatment = getCanvasCctvTreatment(visual.cctvState);

  const bg = ctx.createLinearGradient(x, y, x, y + h);
  bg.addColorStop(0, 'rgba(7,30,32,0.92)');
  bg.addColorStop(1, 'rgba(0,5,7,0.98)');
  roundRect(x, y, w, h, 10, bg, 'rgba(97,255,190,0.12)');

  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.clip();

  ctx.fillStyle = treatment.tint;
  ctx.fillRect(x, y, w, h);
  if (treatment.darkness > 0) {
    ctx.fillStyle = `rgba(0,0,0,${treatment.darkness})`;
    ctx.fillRect(x, y, w, h);
  }

  ctx.strokeStyle = 'rgba(97,255,190,0.11)';
  ctx.lineWidth = 1;
  for (let yy = y + 12; yy < y + h; yy += 22) {
    ctx.beginPath();
    ctx.moveTo(x, yy);
    ctx.lineTo(x + w, yy);
    ctx.stroke();
  }
  for (const ratio of [0.18, 0.5, 0.82]) {
    ctx.beginPath();
    ctx.moveTo(x + w * ratio, y);
    ctx.lineTo(x + w * ratio, y + h);
    ctx.stroke();
  }

  const carW = Math.min(w * 0.42, 150);
  const carH = h * 0.76;
  const jitter = state.moving ? Math.sin(Date.now() / 60) * 2 : 0;
  const carX = x + w / 2 - carW / 2 + jitter;
  const carY = y + h - carH - 8;
  const carFill = ctx.createLinearGradient(carX, carY, carX + carW, carY);
  carFill.addColorStop(0, 'rgba(191,255,240,0.13)');
  carFill.addColorStop(0.5, 'rgba(0,12,14,0.72)');
  carFill.addColorStop(1, 'rgba(191,255,240,0.10)');
  roundRect(carX, carY, carW, carH, 8, carFill, 'rgba(191,255,240,0.42)');

  const open = state.door === 'open';
  const doorGap = open ? carW * 0.18 : 0;
  ctx.fillStyle = 'rgba(97,255,190,0.09)';
  ctx.fillRect(carX + doorGap, carY + 2, carW / 2 - doorGap, carH - 4);
  ctx.fillRect(carX + carW / 2, carY + 2, carW / 2 - doorGap, carH - 4);
  ctx.strokeStyle = 'rgba(97,255,190,0.24)';
  ctx.beginPath();
  ctx.moveTo(carX + carW / 2, carY + 4);
  ctx.lineTo(carX + carW / 2, carY + carH - 4);
  ctx.stroke();

  const heatAlpha = treatment.entity ? 0.98 : state.passengers > 0 ? 0.55 : 0.12;
  const heat = ctx.createRadialGradient(carX + carW / 2, carY + carH * 0.58, 4, carX + carW / 2, carY + carH * 0.58, 34);
  heat.addColorStop(0, `rgba(255,209,102,${heatAlpha})`);
  heat.addColorStop(0.45, `rgba(255,77,109,${heatAlpha * 0.7})`);
  heat.addColorStop(1, 'transparent');
  ctx.fillStyle = heat;
  ctx.fillRect(carX + carW / 2 - 38, carY + carH * 0.28, 76, carH * 0.62);

  roundRect(x + 10, y + h - 28, 58, 20, 8, 'rgba(0,0,0,0.48)', 'rgba(97,255,190,0.24)');
  ctx.fillStyle = COLORS.text;
  ctx.font = 'bold 12px Consolas, monospace';
  ctx.fillText(`F${state.floor}`, x + 18, y + h - 14);

  const reticleX = x + w - 42;
  const reticleY = y + h - 42;
  const reticleThreat = treatment.threat || state.anomalyLevel > 0;
  ctx.strokeStyle = reticleThreat ? 'rgba(255,77,109,0.88)' : 'rgba(97,255,190,0.32)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(reticleX, reticleY, 22 + (reticleThreat ? Math.sin(Date.now() / 120) * 2 : 0), 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(reticleX - 18, reticleY);
  ctx.lineTo(reticleX + 18, reticleY);
  ctx.moveTo(reticleX, reticleY - 18);
  ctx.lineTo(reticleX, reticleY + 18);
  ctx.stroke();

  if (visual.glitch || treatment.glitch) {
    const artifactVisual = treatment.glitch
      ? { ...visual, glitch: true, noise: Math.max(0.72, visual.noise) }
      : visual;
    drawCanvasAnomalyArtifacts(artifactVisual, x, y, w, h);
  }

  ctx.restore();
}

function drawCanvasAnomalyArtifacts(visual, x, y, w, h) {
  const now = Date.now();
  ctx.save();
  ctx.globalCompositeOperation = 'screen';
  ctx.globalAlpha = Math.min(0.9, visual.noise);
  ctx.fillStyle = 'rgba(255,255,255,0.06)';
  for (let i = 0; i < 16; i += 1) {
    const yy = y + ((i * 17 + Math.floor(now / 40) * 9) % h);
    ctx.fillRect(x, yy, w, 1);
  }
  ctx.globalAlpha = 0.42;
  ctx.fillStyle = 'rgba(255,77,109,0.18)';
  ctx.fillRect(x + ((now / 30) % 12) - 6, y + h * 0.32, w, 5);
  ctx.fillStyle = 'rgba(81,214,255,0.16)';
  ctx.fillRect(x - ((now / 34) % 10), y + h * 0.58, w, 4);
  ctx.globalAlpha = visual.tone === 'critical' || visual.tone === 'danger' ? 0.34 : 0.18;
  const infrared = ctx.createRadialGradient(x + w * 0.52, y + h * 0.52, 4, x + w * 0.52, y + h * 0.52, Math.min(w, h) * 0.42);
  infrared.addColorStop(0, 'rgba(255,209,102,0.72)');
  infrared.addColorStop(0.46, 'rgba(255,77,109,0.28)');
  infrared.addColorStop(1, 'transparent');
  ctx.fillStyle = infrared;
  ctx.fillRect(x, y, w, h);
  if (visual.shake) {
    ctx.globalAlpha = 0.22;
    ctx.fillStyle = 'rgba(216,255,243,0.22)';
    ctx.fillRect(x, y, w, h);
  }
  ctx.restore();
}

function getMonitorText(state) {
  const unlockedHidden = state.hiddenLogs.filter(h => !h.locked);
  if (unlockedHidden.length > 0) {
    const last = unlockedHidden[unlockedHidden.length - 1];
    return getDecodedMonitorText(last);
  }
  return state.monitor;
}

export function getCanvasActionButtons(state) {
  const lockedCount = state.hiddenLogs.filter(h => h.locked).length;
  const visual = deriveVisualState(state);
  return getAvailableActions()
    .filter(action => action.id !== 'unlockHiddenLog' || lockedCount > 0)
    .map(action => action.id === 'unlockHiddenLog'
      ? { id: action.id, label: actionLabel(action.id, lockedCount), recommended: visual.highlightAction === action.id }
      : { ...action, recommended: visual.highlightAction === action.id });
}

// ── 绘制操作按钮 ──
function drawActions(state) {
  const layout = getCanvasLayout(DH).actions;
  const { x, y, w, h, columns, gap, buttonW, buttonH, startY } = layout;
  const labels = getCanvasStaticLabels();
  roundRect(x, y, w, h, 6, COLORS.panel, COLORS.line);
  ctx.fillStyle = '#bbb9af';
  ctx.font = 'bold 12px Consolas, "Microsoft YaHei", monospace';
  ctx.fillText(`■ ${labels.actionPanel}`, x + 14, y + 24);

  const btns = getCanvasActionButtons(state).slice(0, 8);
  btns.forEach((btn, i) => {
    const bx = x + 16 + (i % columns) * (buttonW + gap);
    const by = startY + Math.floor(i / columns) * (buttonH + gap);
    const danger = btn.id === 'emergencyStop';
    const fill = ctx.createLinearGradient(0, by, 0, by + buttonH);
    fill.addColorStop(0, danger ? '#492420' : '#2a2f30');
    fill.addColorStop(0.2, danger ? '#321614' : '#1b1f20');
    fill.addColorStop(1, danger ? '#100909' : '#090b0c');
    roundRect(bx, by, buttonW, buttonH, 5, fill, danger ? 'rgba(231,92,79,0.78)' : '#4b504e');
    roundRect(bx + 5, by + 5, buttonW - 10, buttonH - 10, 3, null, 'rgba(0,0,0,0.72)');
    if (btn.recommended) {
      roundRect(bx - 2, by - 2, buttonW + 4, buttonH + 4, 6, null, 'rgba(225,168,75,0.94)');
    }

    ctx.fillStyle = danger ? COLORS.red : COLORS.green;
    ctx.beginPath();
    ctx.arc(bx + buttonW / 2, by + 22, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 15px "Microsoft YaHei", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(btn.label, bx + buttonW / 2, by + 57);
    ctx.fillStyle = COLORS.muted;
    ctx.font = '10px Consolas, monospace';
    ctx.fillText(btn.id.toUpperCase().slice(0, 12), bx + buttonW / 2, by + 74);
    ctx.textAlign = 'left';
  });
}

// ── 绘制系统日志 ──
function drawLogs(state) {
  const { x, y, w, h } = getCanvasLayout(DH).logs;
  const labels = getCanvasStaticLabels();
  roundRect(x, y, w, h, 6, COLORS.panel, COLORS.line);
  ctx.fillStyle = '#bbb9af';
  ctx.font = 'bold 12px Consolas, "Microsoft YaHei", monospace';
  ctx.fillText(`■ ${labels.logPanel}`, x + 14, y + 24);

  const maxRows = Math.max(3, Math.floor((h - 48) / 22));
  const logs = state.logs.slice(-maxRows);
  logs.forEach((log, i) => {
    const lx = x + 18, ly = y + 38 + i * 22;
    const colorMap = { warn: COLORS.amber, danger: COLORS.red, ad: COLORS.cyan, success: COLORS.green };
    ctx.fillStyle = colorMap[log.type] || '#aeb4ad';
    ctx.font = '12px Consolas, "Microsoft YaHei", monospace';
    ctx.fillText(`${i + 1}. ${log.text}`, lx, ly + 12, w - 36);
  });
}

// ── 绘制失败弹窗 ──
function drawFailureOverlay(state) {
  if (!state.gameOver) return;

  // 半透明背景
  ctx.fillStyle = 'rgba(0,0,0,0.72)';
  ctx.fillRect(0, 0, DW, DH);

  const cardW = 620, cardH = 350;
  const cx = (DW - cardW) / 2, cy = (DH - cardH) / 2;

  const labels = getCanvasStaticLabels();
  const copy = getCanvasFailureOverlayCopy(state);
  const isSuccess = state.result === 'success';
  if (!isSuccess && state.fakeEndingTriggered) {
    // 假结局
    roundRect(cx, cy, cardW, cardH, 8, '#211013', 'rgba(231,92,79,0.72)');

    ctx.fillStyle = COLORS.darkRed;
    ctx.font = 'bold 14px "Microsoft YaHei", sans-serif';
    ctx.fillText(copy.eyebrow, cx + 24, cy + 30);

    ctx.fillStyle = '#ff0050';
    ctx.font = 'bold 34px "Microsoft YaHei", sans-serif';
    ctx.fillText(copy.title, cx + 24, cy + 72);

    const text = state.fakeEndingText || '';
    ctx.fillStyle = '#ff6b8a';
    ctx.font = '14px Consolas, "Microsoft YaHei", monospace';
    wrapText(text, cx + 24, cy + 96, cardW - 48, 22);

    if (state.fakeEndingUnlocked) {
      ctx.fillStyle = '#bffff0';
      ctx.font = '14px Consolas, "Microsoft YaHei", monospace';
      const truth = state.fakeEndingTruth || '';
      wrapText(truth, cx + 24, cy + 200, cardW - 48, 22);
    }
  } else {
    roundRect(
      cx,
      cy,
      cardW,
      cardH,
      8,
      '#111415',
      isSuccess ? 'rgba(97,255,190,0.62)' : 'rgba(255,77,109,0.52)',
    );

    ctx.fillStyle = isSuccess ? COLORS.green : COLORS.red;
    ctx.font = 'bold 14px "Microsoft YaHei", sans-serif';
    ctx.fillText(isSuccess ? t('ui.shiftComplete') : copy.eyebrow, cx + 24, cy + 30);

    ctx.fillStyle = isSuccess ? COLORS.green : COLORS.red;
    ctx.font = 'bold 40px "Microsoft YaHei", sans-serif';
    ctx.fillText(isSuccess ? t('ui.shiftComplete') : labels.failureTitle, cx + 24, cy + 80);

    ctx.fillStyle = COLORS.text;
    ctx.font = '16px "Microsoft YaHei", sans-serif';
    const reason = isSuccess ? t('ui.successfulShift') : summarizeFailure(state);
    wrapText(reason, cx + 24, cy + 120, cardW - 48, 24);

    if (!isSuccess && state.lastAdHint) {
      ctx.fillStyle = COLORS.amber;
      ctx.font = '14px "Microsoft YaHei", sans-serif';
      ctx.fillText(copy.adHintLine, cx + 24, cy + 200);
    }
  }

  // 按钮
  const btnY = cy + cardH - 70;
  if (!isSuccess) {
    const btnW2 = (cardW - 60) / 2;
    roundRect(cx + 20, btnY, btnW2, 46, 5, '#17352a', 'rgba(121,214,163,0.7)');
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 16px "Microsoft YaHei", sans-serif';
    ctx.textAlign = 'center';
    const btnLabel = state.fakeEndingTriggered && !state.fakeEndingUnlocked
      ? labels.revealTruth
      : state.fakeEndingTriggered
      ? labels.restart
      : labels.adRevive;
    ctx.fillText(btnLabel, cx + 20 + btnW2 / 2, btnY + 29);
    ctx.textAlign = 'left';

    roundRect(cx + 40 + btnW2, btnY, btnW2, 46, 5, '#202425', 'rgba(195,200,190,0.24)');
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 16px "Microsoft YaHei", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(labels.restart, cx + 40 + btnW2 + btnW2 / 2, btnY + 29);
    ctx.textAlign = 'left';
  } else {
    roundRect(cx + 20, btnY, cardW - 40, 46, 5, '#17352a', 'rgba(121,214,163,0.7)');
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 16px "Microsoft YaHei", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(labels.restart, cx + cardW / 2, btnY + 29);
    ctx.textAlign = 'left';
  }
}

// ── 文字换行 ──
function wrapText(text, x, y, maxWidth, lineHeight) {
  if (!text) return;
  const lines = text.split('\n');
  let cy = y;
  for (const line of lines) {
    let currentLine = '';
    for (const char of line) {
      const testLine = currentLine + char;
      const tw = ctx.measureText(testLine).width;
      if (tw > maxWidth && currentLine) {
        ctx.fillText(currentLine, x, cy);
        currentLine = char;
        cy += lineHeight;
      } else {
        currentLine = testLine;
      }
    }
    if (currentLine) {
      ctx.fillText(currentLine, x, cy);
      cy += lineHeight;
    }
  }
}

// ── 点击检测 ──
let clickHandlers = {};

export function onCanvasClick(x, y, state, callbacks) {
  const { onAdRevive, onRestart, onAction } = callbacks;

  // 失败弹窗按钮检测
  if (state.gameOver) {
    const cardW = 620, cardH = 350;
    const cx2 = (DW - cardW) / 2, cy2 = (DH - cardH) / 2;
    const btnY = cy2 + cardH - 70;
    if (state.result === 'success') {
      if (x >= cx2 + 20 && x <= cx2 + cardW - 20 && y >= btnY && y <= btnY + 46) {
        onRestart?.();
      }
      return;
    }
    const btnW2 = (cardW - 60) / 2;

    // 左按钮
    if (x >= cx2 + 20 && x <= cx2 + 20 + btnW2 && y >= btnY && y <= btnY + 46) {
      if (state.fakeEndingTriggered && !state.fakeEndingUnlocked) {
        onAdRevive?.('truth');
      } else if (state.fakeEndingTriggered) {
        onRestart?.();
      } else {
        onAdRevive?.('revive');
      }
      return;
    }
    // 右按钮
    if (x >= cx2 + 40 + btnW2 && x <= cx2 + 40 + btnW2 * 2 && y >= btnY && y <= btnY + 46) {
      onRestart?.();
      return;
    }
    return;
  }

  // 操作按钮检测 — 与 V3 四列硬件键轨使用同一布局数据。
  const layout = getCanvasLayout(DH).actions;
  const btns = getCanvasActionButtons(state).slice(0, 8).map(button => button.id);
  for (let i = 0; i < btns.length; i += 1) {
    const bx = layout.x + 16 + (i % layout.columns) * (layout.buttonW + layout.gap);
    const by = layout.startY + Math.floor(i / layout.columns) * (layout.buttonH + layout.gap);
    if (x >= bx && x <= bx + layout.buttonW && y >= by && y <= by + layout.buttonH) {
      onAction?.(btns[i]);
      return;
    }
  }
}

// ── 主渲染函数 ──
export function render(state) {
  if (!ctx) return;

  drawBackground();
  drawTopbar(state);
  drawStatusPanel(state);
  drawMonitor(state);
  drawActions(state);
  drawLogs(state);
  drawFailureOverlay(state);
}

// ── 初始化 ──
export function init(canvasEl) {
  canvas = canvasEl;
  ctx = canvas.getContext('2d');

  const info = { windowWidth: DW, windowHeight: DH, pixelRatio: 1 };
  const pw = info.windowWidth || DW;
  const ph = info.windowHeight || DH;

  // 保持设计比例
  DH = Math.max(1334, ph * (DW / pw));

  canvas.width = DW;
  canvas.height = DH;
  scale = 1;

  return { width: DW, height: DH };
}

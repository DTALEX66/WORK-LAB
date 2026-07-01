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
import { getToneForState, summarizeFailure } from '../src/feedback.js';
import { getDecodedMonitorText, getDirectionLabel, getDomLabels, getDoorLabel } from '../src/uiLabels.js';

// ── 尺寸常量 ──
const DW = 750;       // 设计宽度
let canvas, ctx;
let scale = 1;        // 实际像素/设计像素比例
let DH = 1334;        // 设计高度（自适应）

// ── 颜色 ──
const COLORS = {
  bg: '#05080b',
  panel: 'rgba(8,18,21,0.92)',
  line: 'rgba(97,255,190,0.22)',
  text: '#d8fff3',
  muted: '#789b92',
  green: '#61ffbe',
  amber: '#ffd166',
  red: '#ff4d6d',
  cyan: '#51d6ff',
  darkRed: '#ff0050',
};

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
function drawBackground(tone) {
  // 纯色背景
  ctx.fillStyle = COLORS.bg;
  ctx.fillRect(0, 0, DW, DH);

  // 径向渐变装饰
  const grad1 = ctx.createRadialGradient(150, 0, 0, 150, 0, 400);
  grad1.addColorStop(0, 'rgba(81,214,255,0.10)');
  grad1.addColorStop(1, 'transparent');
  ctx.fillStyle = grad1;
  ctx.fillRect(0, 0, DW, DH);

  const grad2 = ctx.createRadialGradient(DW - 100, 100, 0, DW - 100, 100, 350);
  grad2.addColorStop(0, 'rgba(255,77,109,0.10)');
  grad2.addColorStop(1, 'transparent');
  ctx.fillStyle = grad2;
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
  const meta = getSkin().meta;
  ctx.fillStyle = COLORS.text;
  ctx.font = 'bold 22px "Microsoft YaHei", sans-serif';
  ctx.fillText(meta?.name || '', 24, 44);

  ctx.fillStyle = COLORS.green;
  ctx.font = '14px "Microsoft YaHei", sans-serif';
  ctx.fillText(meta?.subtitle || '', 24, 64);

  const labels = getCanvasStaticLabels();
  // 倒计时卡片
  const cardX = DW - 170;
  const cardW = 150;
  roundRect(cardX, 14, cardW, 50, 14, COLORS.panel, COLORS.line);
  ctx.fillStyle = COLORS.muted;
  ctx.font = '12px "Microsoft YaHei", sans-serif';
  ctx.fillText(labels.countdown, cardX + 12, 32);
  ctx.fillStyle = COLORS.amber;
  ctx.font = 'bold 28px "Microsoft YaHei", sans-serif';
  ctx.textAlign = 'right';
  ctx.fillText(Math.ceil(state.remaining).toString(), cardX + cardW - 14, 53);
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
  const x = 14, y = 80, w = 260, h = 220;

  // 面板背景
  roundRect(x, y, w, h, 16, COLORS.panel, toneBorder(state));

  ctx.fillStyle = COLORS.green;
  ctx.font = 'bold 13px "Microsoft YaHei", sans-serif';
  ctx.fillText(getCanvasStatusPanelTitle(), x + 16, y + 28);

  // 状态网格（2列）
  const items = getCanvasStatusItems(state);

  const colW = (w - 32) / 2;
  items.forEach(({ label, value }, i) => {
    const cx = x + 16 + (i % 2) * colW;
    const cy = y + 44 + Math.floor(i / 2) * 26;

    roundRect(cx, cy, colW - 8, 22, 8, 'rgba(0,0,0,0.18)', 'rgba(255,255,255,0.08)');
    ctx.fillStyle = COLORS.muted;
    ctx.font = '11px "Microsoft YaHei", sans-serif';
    ctx.fillText(label, cx + 8, cy + 15);
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 14px "Microsoft YaHei", sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(String(value), cx + colW - 12, cy + 15);
    ctx.textAlign = 'left';
  });

  getCanvasMeterBars(state).forEach(({ label, value, color }, index) => {
    drawBar(x + 16, y + 175 + index * 21, w - 32, 16, label, value, color);
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
  const tone = getToneForState(state);
  if (tone === 'danger') return 'rgba(255,77,109,0.55)';
  if (tone === 'critical') return 'rgba(255,209,102,0.38)';
  if (tone === 'warn') return 'rgba(255,209,102,0.38)';
  return COLORS.line;
}

// ── 绘制监控画面 ──
function drawMonitor(state) {
  const x = 286, y = 80, w = 448, h = 220;

  const labels = getCanvasStaticLabels();
  roundRect(x, y, w, h, 16, COLORS.panel, toneBorder(state));
  ctx.fillStyle = COLORS.green;
  ctx.font = 'bold 13px "Microsoft YaHei", sans-serif';
  ctx.fillText(labels.monitorPanel, x + 16, y + 28);

  // 监控内容区域：视觉画面 + 字幕，不再只是大段文字
  const mx = x + 14, my = y + 38, mw = w - 28, mh = h - 50;
  roundRect(mx, my, mw, mh, 12, 'rgba(0,0,0,0.2)', 'rgba(97,255,190,0.12)');
  drawCctvScene(state, mx + 10, my + 10, mw - 20, mh - 58);

  // 扫描线效果
  const scanY = (Date.now() / 100 * mh) % mh;
  ctx.fillStyle = 'rgba(97,255,190,0.04)';
  ctx.fillRect(mx, my + scanY, mw, 4);

  // 字幕文本
  let displayText = getMonitorText(state);
  ctx.fillStyle = '#bffff0';
  ctx.font = '13px "Microsoft YaHei", sans-serif';
  ctx.textAlign = 'center';
  wrapText(displayText, mx + mw / 2, my + mh - 34, mw - 24, 17);
  ctx.textAlign = 'left';
}

function drawCctvScene(state, x, y, w, h) {
  if (h <= 20) return;

  const bg = ctx.createLinearGradient(x, y, x, y + h);
  bg.addColorStop(0, 'rgba(7,30,32,0.92)');
  bg.addColorStop(1, 'rgba(0,5,7,0.98)');
  roundRect(x, y, w, h, 10, bg, 'rgba(97,255,190,0.12)');

  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.clip();

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

  const heatAlpha = state.passengers > 0 ? 0.9 : 0.18;
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
  ctx.strokeStyle = state.anomalyLevel > 0 ? 'rgba(255,77,109,0.88)' : 'rgba(97,255,190,0.32)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(reticleX, reticleY, 22 + (state.anomalyLevel > 0 ? Math.sin(Date.now() / 120) * 2 : 0), 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(reticleX - 18, reticleY);
  ctx.lineTo(reticleX + 18, reticleY);
  ctx.moveTo(reticleX, reticleY - 18);
  ctx.lineTo(reticleX, reticleY + 18);
  ctx.stroke();

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
  return getAvailableActions()
    .filter(action => action.id !== 'unlockHiddenLog' || lockedCount > 0)
    .map(action => action.id === 'unlockHiddenLog'
      ? { id: action.id, label: actionLabel(action.id, lockedCount) }
      : action);
}

// ── 绘制操作按钮 ──
function drawActions(state) {
  const x = 14, y = 312, w = 260, h = 260;

  const labels = getCanvasStaticLabels();
  roundRect(x, y, w, h, 16, COLORS.panel, COLORS.line);
  ctx.fillStyle = COLORS.green;
  ctx.font = 'bold 13px "Microsoft YaHei", sans-serif';
  ctx.fillText(labels.actionPanel, x + 16, y + 28);

  const btns = getCanvasActionButtons(state);

  const btnW = (w - 40) / 2;
  const btnH = 40;
  const gap = 10;
  const startY = y + 42;

  btns.forEach((btn, i) => {
    const bx = x + 16 + (i % 2) * (btnW + gap);
    const by = startY + Math.floor(i / 2) * (btnH + gap);

    const isGreen = !['emergencyStop', 'restartSystem'].includes(btn.id);
    const color = isGreen
      ? 'linear-gradient(135deg, #61ffbe, #51d6ff)'
      : 'rgba(255,255,255,0.08)';

    // 按钮背景
    roundRect(bx, by, btnW, btnH, 10, color);
    if (!isGreen) {
      ctx.strokeStyle = 'rgba(255,255,255,0.12)';
      ctx.lineWidth = 1;
      roundRect(bx, by, btnW, btnH, 10, null, 'rgba(255,255,255,0.12)');
    }

    ctx.fillStyle = isGreen ? '#02110c' : COLORS.text;
    ctx.font = 'bold 13px "Microsoft YaHei", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(btn.label, bx + btnW / 2, by + btnH / 2 + 5);
    ctx.textAlign = 'left';
  });

  // 触发异常测试按钮
  const testBtnY = startY + Math.ceil(btns.length / 2) * (btnH + gap) + 6;
  roundRect(x + 16, testBtnY, w - 32, 34, 10, 'rgba(255,255,255,0.08)', 'rgba(255,255,255,0.12)');
  ctx.fillStyle = COLORS.text;
  ctx.font = '12px "Microsoft YaHei", sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(labels.forceAnomaly, x + w / 2, testBtnY + 22);
  ctx.textAlign = 'left';
}

// ── 绘制系统日志 ──
function drawLogs(state) {
  const x = 286, y = 312, w = 448, h = 260;

  const labels = getCanvasStaticLabels();
  roundRect(x, y, w, h, 16, COLORS.panel, COLORS.line);
  ctx.fillStyle = COLORS.green;
  ctx.font = 'bold 13px "Microsoft YaHei", sans-serif';
  ctx.fillText(labels.logPanel, x + 16, y + 28);

  const logs = state.logs.slice(-12);
  const logY = y + 38;
  logs.forEach((log, i) => {
    const lx = x + 16, ly = logY + i * 19;
    const colorMap = { warn: COLORS.amber, danger: COLORS.red, ad: COLORS.cyan, success: COLORS.green };
    ctx.fillStyle = colorMap[log.type] || '#bfeee0';
    ctx.font = '12px Consolas, "Microsoft YaHei", monospace';
    ctx.fillText(log.text, lx, ly + 12);
  });
}

// ── 绘制失败弹窗 ──
function drawFailureOverlay(state) {
  if (!state.gameOver) return;

  // 半透明背景
  ctx.fillStyle = 'rgba(0,0,0,0.72)';
  ctx.fillRect(0, 0, DW, DH);

  const cardW = 520, cardH = 320;
  const cx = (DW - cardW) / 2, cy = (DH - cardH) / 2;

  const labels = getCanvasStaticLabels();
  const copy = getCanvasFailureOverlayCopy(state);
  if (state.fakeEndingTriggered) {
    // 假结局
    roundRect(cx, cy, cardW, cardH, 24, 'rgba(60,0,12,0.98)', 'rgba(255,0,80,0.7)');

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
    // 正常失败
    roundRect(cx, cy, cardW, cardH, 24, 'rgba(38,5,12,0.98)', 'rgba(255,77,109,0.52)');

    ctx.fillStyle = COLORS.red;
    ctx.font = 'bold 14px "Microsoft YaHei", sans-serif';
    ctx.fillText(copy.eyebrow, cx + 24, cy + 30);

    ctx.fillStyle = COLORS.red;
    ctx.font = 'bold 40px "Microsoft YaHei", sans-serif';
    ctx.fillText(labels.failureTitle, cx + 24, cy + 80);

    ctx.fillStyle = COLORS.text;
    ctx.font = '16px "Microsoft YaHei", sans-serif';
    const reason = summarizeFailure(state);
    wrapText(reason, cx + 24, cy + 120, cardW - 48, 24);

    if (state.lastAdHint) {
      ctx.fillStyle = COLORS.amber;
      ctx.font = '14px "Microsoft YaHei", sans-serif';
      ctx.fillText(copy.adHintLine, cx + 24, cy + 200);
    }
  }

  // 按钮
  const btnY = cy + cardH - 70;
  const btnW2 = (cardW - 60) / 2;
  // 左按钮（广告复活）
  roundRect(cx + 20, btnY, btnW2, 46, 12, COLORS.green);
  ctx.fillStyle = '#02110c';
  ctx.font = 'bold 16px "Microsoft YaHei", sans-serif';
  ctx.textAlign = 'center';
  const btnLabel = state.fakeEndingTriggered && !state.fakeEndingUnlocked
    ? labels.revealTruth
    : state.fakeEndingTriggered
    ? labels.restart
    : labels.adRevive;
  ctx.fillText(btnLabel, cx + 20 + btnW2 / 2, btnY + 29);
  ctx.textAlign = 'left';

  // 右按钮（重新开始）
  roundRect(cx + 40 + btnW2, btnY, btnW2, 46, 12, 'rgba(255,255,255,0.08)', 'rgba(255,255,255,0.12)');
  ctx.fillStyle = COLORS.text;
  ctx.font = 'bold 16px "Microsoft YaHei", sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(labels.restart, cx + 40 + btnW2 + btnW2 / 2, btnY + 29);
  ctx.textAlign = 'left';
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
  const { onAdRevive, onRestart, onAction, onForceAnomaly } = callbacks;

  // 失败弹窗按钮检测
  if (state.gameOver) {
    const cardW = 520, cardH = 320;
    const cx2 = (DW - cardW) / 2, cy2 = (DH - cardH) / 2;
    const btnY = cy2 + cardH - 70;
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

  // 操作按钮检测
  const btnW = (260 - 40) / 2;
  const btnH2 = 40;
  const gap = 10;
  const startY = 312 + 42;

  const btns = getCanvasActionButtons(state).map(button => button.id);

  for (let i = 0; i < btns.length; i++) {
    const bx = 14 + 16 + (i % 2) * (btnW + gap);
    const by = startY + Math.floor(i / 2) * (btnH2 + gap);
    if (x >= bx && x <= bx + btnW && y >= by && y <= by + btnH2) {
      onAction?.(btns[i]);
      return;
    }
  }

  // 触发异常测试按钮
  const testBtnY = startY + Math.ceil(btns.length / 2) * (btnH2 + gap) + 6;
  if (x >= 14 + 16 && x <= 14 + 16 + (260 - 32) && y >= testBtnY && y <= testBtnY + 34) {
    onForceAnomaly?.();
  }
}

// ── 主渲染函数 ──
export function render(state) {
  if (!ctx) return;

  const tone = getToneForState(state);
  drawBackground(tone);
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

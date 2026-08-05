/**
 * audio.js — 程序化音效（Web Audio API，无需外部文件）
 *
 * 所有声音通过 OscillatorNode + GainNode 实时合成，
 * 初始化为惰性加载，首次用户交互时才会创建 AudioContext。
 */

let ctx = null;

function getContext() {
  if (!ctx) {
    ctx = new (window.AudioContext || window.webkitAudioContext)();
  }
  // 某些浏览器在 user gesture 后需要 resume
  if (ctx.state === 'suspended') {
    ctx.resume().catch(() => {});
  }
  return ctx;
}

/**
 * 播放一个简单的单频音
 * @param {number} freq - 频率 Hz
 * @param {number} duration - 持续秒
 * @param {string} type - 波形类型
 * @param {number} volume - 音量 0-1
 */
function beep(freq, duration, type = 'square', volume = 0.08) {
  try {
    const ac = getContext();
    const osc = ac.createOscillator();
    const gain = ac.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, ac.currentTime);
    gain.gain.setValueAtTime(volume, ac.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + duration);
    osc.connect(gain);
    gain.connect(ac.destination);
    osc.start(ac.currentTime);
    osc.stop(ac.currentTime + duration);
  } catch {
    // 静默失败 — 音效不是关键功能
  }
}

/**
 * 播放一个扫频音（用于异常/警报）
 */
function sweep(startFreq, endFreq, duration, type = 'sawtooth', volume = 0.06) {
  try {
    const ac = getContext();
    const osc = ac.createOscillator();
    const gain = ac.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(startFreq, ac.currentTime);
    osc.frequency.exponentialRampToValueAtTime(endFreq, ac.currentTime + duration);
    gain.gain.setValueAtTime(volume, ac.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + duration);
    osc.connect(gain);
    gain.connect(ac.destination);
    osc.start(ac.currentTime);
    osc.stop(ac.currentTime + duration);
  } catch {
    // 静默失败
  }
}

/** 按钮点击 — 短促的咔嗒声 */
export function playClick() {
  beep(800, 0.06, 'square', 0.06);
}

/** 操作成功 — 确认音 */
export function playSuccess() {
  beep(1000, 0.1, 'sine', 0.07);
}

/** 操作失败 — 拒绝音 */
export function playFail() {
  beep(300, 0.18, 'sawtooth', 0.07);
}

/** 异常触发 — 低频警报扫频 */
export function playAnomaly() {
  sweep(200, 80, 0.45, 'sawtooth', 0.08);
}

/** 稳定度/电源危险 — 短促警告 */
export function playWarning() {
  sweep(600, 200, 0.25, 'square', 0.06);
}

/** 系统崩溃 — 低沉衰减 */
export function playCrash() {
  sweep(150, 30, 0.8, 'sawtooth', 0.1);
}

/** 广告复活 — 上升恢复音 */
export function playRevive() {
  sweep(200, 1200, 0.5, 'sine', 0.08);
}

/** 游戏重启 — 重置音 */
export function playRestart() {
  beep(600, 0.08, 'sine', 0.06);
  setTimeout(() => beep(800, 0.1, 'sine', 0.06), 100);
}

import { appendLog, checkFailure, clamp, cloneState } from './state.js';
import CONFIG from './gameConfig.js';
import { getAnomalies, getHiddenLog as _getHiddenLog, t } from './skinManager.js';

/**
 * 从皮肤数据动态构建异常事件数组
 */
function createAnomaly(skinDef) {
  return {
    id: skinDef.id,
    title: skinDef.title,
    severity: skinDef.severity,
    monitor: skinDef.monitor,
    adHint: skinDef.adHint,
    apply(state) {
      const next = cloneState(state);
      const effects = skinDef.effects || {};
      for (const [field, value] of Object.entries(effects)) {
        if (field === 'floor' && typeof value === 'string' && value.startsWith('+')) {
          // floor 的 '+X' 字符串 → 增量累加并封顶
          const num = parseInt(value, 10);
          next[field] = Math.min(30, (next[field] ?? 0) + num);
        } else if (field === 'floor' || field === 'passengers' || field === 'door') {
          // 绝对赋值（floor 数值、passengers、door）
          next[field] = value;
        } else if (typeof value === 'number') {
          // 数值累加（anomalyLevel、stability、power 等）
          next[field] = (next[field] ?? 0) + value;
        } else if (typeof value === 'string' && value.startsWith('+')) {
          // 其他 '+X' 字符串：增量累加
          next[field] = (next[field] ?? 0) + parseInt(value, 10);
        } else {
          // 其他字符串：直接赋值
          next[field] = value;
        }
      }
      next.anomalyLevel = clamp(next.anomalyLevel, 0, 6);
      next.stability = clamp(next.stability, 0, 100);
      next.power = clamp(next.power, 0, 100);
      next.activeAnomaly = skinDef.id;
      next.monitor = skinDef.monitor;
      return next;
    },
  };
}

/** 当前皮肤生成的异常事件列表 */
export const ANOMALIES = getAnomalies().map(createAnomaly);

export function findAnomaly(id) {
  return ANOMALIES.find((event) => event.id === id);
}

export function applyAnomaly(state, id) {
  const event = findAnomaly(id);
  if (!event) throw new Error(`Unknown anomaly: ${id}`);
  let next = event.apply(state);
  next.lastAdHint = event.adHint;
  // 添加关联隐藏日志（不重复）
  const raw = _getHiddenLog(id);
  if (raw && !next.hiddenLogs.some(h => h.id === id + '_log')) {
    next.hiddenLogs.push({ id: id + '_log', title: raw.title, content: raw.content, locked: true });
    next = appendLog(next, 'info', t('ui.hiddenLogCaptured', { title: raw.title }));
  }
  next = appendLog(next, event.severity >= 3 ? 'danger' : 'warn', `异常事件：${event.title}。${event.adHint}`);
  return { event, state: checkFailure(next) };
}

export function pickNextAnomaly(state, random = Math.random) {
  const pressure = Math.min(ANOMALIES.length - 1, Math.floor(state.anomalyLevel / CONFIG.anomaly.pressureDivisor));
  const index = Math.min(ANOMALIES.length - 1, Math.floor(random() * ANOMALIES.length + pressure) % ANOMALIES.length);
  return ANOMALIES[index];
}

// 向后兼容导出
export function getHiddenLog(anomalyId) {
  return _getHiddenLog(anomalyId);
}

/** @deprecated 请使用 getHiddenLog() 代替 */
const _buildHiddenLogsMap = () => {
  const map = {};
  const anomalies = getAnomalies();
  for (const a of anomalies) {
    const hl = _getHiddenLog(a.id);
    if (hl) {
      map[a.id] = { id: `${a.id}_log`, title: hl.title, content: hl.content };
    }
  }
  return map;
};

export const HIDDEN_LOGS = _buildHiddenLogsMap();

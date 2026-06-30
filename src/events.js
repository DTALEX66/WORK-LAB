import { appendLog, checkFailure, clamp, cloneState } from './state.js';

export const ANOMALIES = [
  {
    id: 'phantom_floor',
    title: '不存在的楼层',
    severity: 2,
    monitor: '监控：电梯停在 13 层。建筑图纸中不存在该楼层。',
    adHint: '当楼层显示 13 时，不要开门，先执行系统重启。',
    apply(state) {
      const next = cloneState(state);
      next.floor = 13;
      next.anomalyLevel = clamp(next.anomalyLevel + 2, 0, 6);
      next.stability = clamp(next.stability - 10, 0, 100);
      next.activeAnomaly = 'phantom_floor';
      next.monitor = this.monitor;
      return next;
    },
  },
  {
    id: 'camera_delay',
    title: '监控延迟',
    severity: 1,
    monitor: '监控：画面延迟 3 秒。乘客动作与控制台记录不同步。',
    adHint: '监控延迟时优先查看日志，不要连续移动。',
    apply(state) {
      const next = cloneState(state);
      next.anomalyLevel = clamp(next.anomalyLevel + 1, 0, 6);
      next.stability = clamp(next.stability - 6, 0, 100);
      next.activeAnomaly = 'camera_delay';
      next.monitor = this.monitor;
      return next;
    },
  },
  {
    id: 'zero_passenger_shadow',
    title: '门外有人但乘客数为 0',
    severity: 2,
    monitor: '监控：门外站着一个人，但乘客计数器显示 0。',
    adHint: '乘客数异常时保持关门，先急停再查日志。',
    apply(state) {
      const next = cloneState(state);
      next.passengers = 0;
      next.anomalyLevel = clamp(next.anomalyLevel + 2, 0, 6);
      next.stability = clamp(next.stability - 12, 0, 100);
      next.activeAnomaly = 'zero_passenger_shadow';
      next.monitor = this.monitor;
      return next;
    },
  },
  {
    id: 'log_echo',
    title: '系统日志重复字符',
    severity: 1,
    monitor: '监控：系统日志开始重复输出“不要开门”。',
    adHint: '日志重复通常是轻度异常，系统重启可降低异常等级。',
    apply(state) {
      const next = cloneState(state);
      next.anomalyLevel = clamp(next.anomalyLevel + 1, 0, 6);
      next.stability = clamp(next.stability - 5, 0, 100);
      next.activeAnomaly = 'log_echo';
      next.monitor = this.monitor;
      return next;
    },
  },
  {
    id: 'auto_button',
    title: '按钮自动亮起',
    severity: 2,
    monitor: '监控：没有乘客触碰按钮，B2 与 9 层按钮自动亮起。',
    adHint: '按钮自动亮起时不要跟随请求移动，先关门并急停。',
    apply(state) {
      const next = cloneState(state);
      next.anomalyLevel = clamp(next.anomalyLevel + 2, 0, 6);
      next.power = clamp(next.power - 8, 0, 100);
      next.activeAnomaly = 'auto_button';
      next.monitor = this.monitor;
      return next;
    },
  },
  {
    id: 'stop_failure',
    title: '急停按钮失效',
    severity: 3,
    monitor: '监控：急停按钮指示灯熄灭，控制台拒绝确认安全回路。',
    adHint: '急停失效时不要反复点击，优先系统重启。',
    apply(state) {
      const next = cloneState(state);
      next.anomalyLevel = clamp(next.anomalyLevel + 3, 0, 6);
      next.stability = clamp(next.stability - 15, 0, 100);
      next.activeAnomaly = 'stop_failure';
      next.monitor = this.monitor;
      return next;
    },
  },
  {
    id: 'negative_floor',
    title: '楼层显示为负数',
    severity: 2,
    monitor: '监控：楼层显示 -1。摄像头画面出现地下走廊。',
    adHint: '负数楼层不是正常地下层，立即重启系统。',
    apply(state) {
      const next = cloneState(state);
      next.floor = -1;
      next.anomalyLevel = clamp(next.anomalyLevel + 2, 0, 6);
      next.stability = clamp(next.stability - 10, 0, 100);
      next.activeAnomaly = 'negative_floor';
      next.monitor = this.monitor;
      return next;
    },
  },
  {
    id: 'power_drain',
    title: '电源异常下降',
    severity: 2,
    monitor: '监控：备用电源自动接管，但电量仍在下降。',
    adHint: '电源异常下降时减少移动，优先关门与重启。',
    apply(state) {
      const next = cloneState(state);
      next.power = clamp(next.power - 22, 0, 100);
      next.anomalyLevel = clamp(next.anomalyLevel + 2, 0, 6);
      next.activeAnomaly = 'power_drain';
      next.monitor = this.monitor;
      return next;
    },
  },
];

export function findAnomaly(id) {
  return ANOMALIES.find((event) => event.id === id);
}

export function applyAnomaly(state, id) {
  const event = findAnomaly(id);
  if (!event) throw new Error(`Unknown anomaly: ${id}`);
  let next = event.apply(state);
  next.lastAdHint = event.adHint;
  next = appendLog(next, event.severity >= 3 ? 'danger' : 'warn', `异常事件：${event.title}。${event.adHint}`);
  return { event, state: checkFailure(next) };
}

export function pickNextAnomaly(state, random = Math.random) {
  const pressure = Math.min(ANOMALIES.length - 1, Math.floor(state.anomalyLevel / 2));
  const index = Math.min(ANOMALIES.length - 1, Math.floor(random() * ANOMALIES.length + pressure) % ANOMALIES.length);
  return ANOMALIES[index];
}

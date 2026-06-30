import { appendLog, checkFailure, clamp, cloneState } from './state.js';
import CONFIG from './gameConfig.js';

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
  {
    id: 'door_refuse',
    title: '电梯门拒绝关闭',
    severity: 2,
    monitor: '监控：关门按钮已按下，门在合拢前自动弹开。异常状态持续。',
    adHint: '门拒绝关闭时不要连续按关门，先急停再重启系统。',
    apply(state) {
      const next = cloneState(state);
      next.door = 'open';
      next.anomalyLevel = clamp(next.anomalyLevel + 2, 0, 6);
      next.stability = clamp(next.stability - 10, 0, 100);
      next.activeAnomaly = 'door_refuse';
      next.monitor = this.monitor;
      return next;
    },
  },
  {
    id: 'weight_mismatch',
    title: '载重数据异常',
    severity: 1,
    monitor: '监控：载重传感器读数 — 0kg。轿厢内有 1 名乘客。读数矛盾。',
    adHint: '载重异常时优先查日志，乘客数可能被重置。',
    apply(state) {
      const next = cloneState(state);
      next.passengers = 0;
      next.anomalyLevel = clamp(next.anomalyLevel + 1, 0, 6);
      next.stability = clamp(next.stability - 7, 0, 100);
      next.activeAnomaly = 'weight_mismatch';
      next.monitor = this.monitor;
      return next;
    },
  },
  {
    id: 'floor_jump',
    title: '楼层编号跳跃',
    severity: 2,
    monitor: '监控：电梯从 5 层直接移动到 9 层。摄像头画面缺失 4 帧。',
    adHint: '楼层跳跃时减少移动操作，用系统重启恢复楼层显示。',
    apply(state) {
      const next = cloneState(state);
      next.floor = Math.min(30, next.floor + 4);
      next.anomalyLevel = clamp(next.anomalyLevel + 2, 0, 6);
      next.stability = clamp(next.stability - 12, 0, 100);
      next.power = clamp(next.power - 10, 0, 100);
      next.activeAnomaly = 'floor_jump';
      next.monitor = this.monitor;
      return next;
    },
  },
  {
    id: 'emergency_lights',
    title: '应急灯异常启动',
    severity: 3,
    monitor: '监控：轿厢应急灯突然亮起。备用电源消耗加速。',
    adHint: '应急灯启动时尽量避免移动，立即重启系统可关闭应急灯。',
    apply(state) {
      const next = cloneState(state);
      next.anomalyLevel = clamp(next.anomalyLevel + 3, 0, 6);
      next.stability = clamp(next.stability - 14, 0, 100);
      next.power = clamp(next.power - 20, 0, 100);
      next.activeAnomaly = 'emergency_lights';
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
  // 添加关联隐藏日志（不重复）
  const hidden = HIDDEN_LOGS[id];
  if (hidden && !next.hiddenLogs.some(h => h.id === hidden.id)) {
    next.hiddenLogs.push({ ...hidden, locked: true });
    next = appendLog(next, 'info', `加密记录已捕获：${hidden.title}。使用"查看日志"功能解码。`);
  }
  next = appendLog(next, event.severity >= 3 ? 'danger' : 'warn', `异常事件：${event.title}。${event.adHint}`);
  return { event, state: checkFailure(next) };
}

export function pickNextAnomaly(state, random = Math.random) {
  const pressure = Math.min(ANOMALIES.length - 1, Math.floor(state.anomalyLevel / CONFIG.anomaly.pressureDivisor));
  const index = Math.min(ANOMALIES.length - 1, Math.floor(random() * ANOMALIES.length + pressure) % ANOMALIES.length);
  return ANOMALIES[index];
}

/**
 * 隐藏日志映射 — 每个异常关联一条加密记录
 * 首次触发异常时自动加入 state.hiddenLogs
 */
export const HIDDEN_LOGS = {
  phantom_floor: {
    id: 'phantom_floor_log',
    title: '第13层施工记录',
    content: '2019年施工记录：第13层在竣工前被从建筑图纸中删除。\n原因：施工期间发生Ⅲ级安全事件，3名工人失踪。\n楼层控制面板已被物理封堵，但系统仍能响应来自该层的按钮信号。',
  },
  camera_delay: {
    id: 'camera_delay_log',
    title: '监控系统校准记录',
    content: '校准日志 #4417：摄像头#03 与#07 存在 3 秒信号延迟。\n技术人员备注："延迟与第 13 层信号干扰有关，建议不要在 13 层停靠。"',
  },
  zero_passenger_shadow: {
    id: 'zero_passenger_log',
    title: '乘客记录异常说明',
    content: '传感器技术手册（节选）：\n红外传感器在非营业时段多次检测到热源信号，但乘客计数器持续归零。\n维修记录：传感器无故障。热源信号经比对——与员工体温档案不匹配。',
  },
  log_echo: {
    id: 'log_echo_log',
    title: '日志系统诊断报告',
    content: '诊断报告 #FD-22-019：\n系统日志缓冲区检测到重复写入操作。重复内容"不要开门"的写入时间戳早于当前值班员登录时间。\n建议：检查前一值班员的退出状态。',
  },
  auto_button: {
    id: 'auto_button_log',
    title: '控制系统审计追踪',
    content: '审计追踪 #AUD-882：\n自动按钮信号来源追溯至 5 号服务器（已于 2022 年停用）。\n该服务器的最后一条记录："控制权移交程序未完成"。',
  },
  stop_failure: {
    id: 'stop_failure_log',
    title: '急停系统维护日志',
    content: '维护日志 #M-341：\n急停回路#2 在定期检查中被标记为"状态：不可用"。\n签署人签名无法识别。签署时间：3 年前。没有后续维修记录。',
  },
  negative_floor: {
    id: 'negative_floor_log',
    title: '地下层勘测报告',
    content: '建筑勘测报告（内部）：\n地下实际存在 4 层结构，但公开图纸仅标注 B1-B2。\nB3-B4 的电梯按钮在出厂时已被移除，但线路仍然通电。',
  },
  power_drain: {
    id: 'power_drain_log',
    title: '备用电源异常报告',
    content: '异常报告 #P-877：\n备用电源在无负载状态下持续放电。经查，有一条非授权线路从备用电源柜分接至未知设备。\n线路标签："不要切断"。',
  },
  door_refuse: {
    id: 'door_refuse_log',
    title: '门控系统事故报告',
    content: '事故报告 #D-1290：\n门控模块在连续 3 次异常重启后进入保护模式。\n模块日志输出最后一条："识别到外部干扰信号。拒绝执行 — 保护乘员安全。"',
  },
  weight_mismatch: {
    id: 'weight_mismatch_log',
    title: '传感器校验记录',
    content: '校验记录 #W-554：\n载重传感器与红外传感器读数不一致。红外传感器在轿厢空载时检测到热源。\n技术人员备注："请确认值班员在操作前已清空轿厢。"',
  },
  floor_jump: {
    id: 'floor_jump_log',
    title: '楼层定位日志',
    content: '定位日志 #F-213：\nGPS 楼层定位模块在校准前后记录的楼层编号不一致。\n系统自动修正失败。可能原因：参考信号源来自非标设备。',
  },
  emergency_lights: {
    id: 'emergency_lights_log',
    title: '应急照明测试报告',
    content: '测试报告 #E-777：\n应急照明系统在无触发信号的情况下自行启动。\n供电线路检测到寄生回路。回路终端设备编号无法匹配任何已知设备清单。',
  },
};

/** 获取异常关联的隐藏日志（没有则返回 null） */
export function getHiddenLog(anomalyId) {
  return HIDDEN_LOGS[anomalyId] || null;
}

/**
 * MINIGAME - 微信 小游戏构建
 * 构建标记: deterministic
 * 请勿手动修改此文件
 */
(function() {
'use strict';

// --- src/gameConfig.js ---
/**
 * gameConfig.js — MINIGAME 平衡参数配置（单一配置源）
 *
 * v2.0 平衡调优：
 * - 更平滑的难度曲线
 * - 操作策略深度加深
 * - 新手友好但高手有挑战
 *
 * 用法：
 *   import CONFIG from './gameConfig.js';
 *   CONFIG.tick.powerDrainMoving  // 0.5
 */

const CONFIG = {
  /* ── 初始状态 ── */
  initial: {
    floor: 1,
    door: 'closed',
    moving: false,
    direction: 'idle',
    power: 100,
    stability: 100,
    anomalyLevel: 0,
    passengers: 1,
    gameOver: false,
    duration: 60,          // 值守倒计时（秒）
  },

  /* ── 每 Tick（1 秒）消耗 ── */
  tick: {
    powerDrainMoving: 0.5,    // 移动中每秒电源消耗（↓0.7）
    powerDrainIdle: 0.15,     // 待机每秒电源消耗（↓0.18）
    stabilityDrainMoving: 0.2, // 移动中每秒稳定度消耗（↓0.25）
  },

  /* ── 操作消耗/效果 ── */
  actions: {
    moveUp: {
      powerCost: 5,           // ↓6
      stabilityCost: 1.5,     // ↓2
    },
    moveDown: {
      powerCost: 5,           // ↓6
      stabilityCost: 1.5,     // ↓2
    },
    emergencyStop: {
      stabilityCost: 4,       // ↓6
      stabilityCostOnFailure: 12, // ↓16 急停失效时的额外惩罚
    },
    restartSystem: {
      anomalyLevelReduce: 2,
      stabilityRestore: 20,   // ↑15 更值得用
      powerCost: 8,           // ↓10
    },
  },

  /* ── 失败条件 ── */
  failure: {
    powerMin: 0,
    stabilityMin: 0,
    anomalyLevelMax: 6,
    passengersMin: 0,
  },

  /* ── 世界边界 ── */
  bounds: {
    maxFloor: 30,
  },

  /* ── 异常系统 ── */
  anomaly: {
    firstTriggerAt: 14,         // 首次异常触发 ↑12（更多准备时间）
    cooldownMin: 10,            // 异常后最短冷却 ↑8
    cooldownMax: 18,            // 异常后最长冷却 ↑13（更多节奏变化）
    pressureDivisor: 2,         // pickNextAnomaly 压力算法分母

    // 难度递增：每 elapsedSeconds 的异常效果乘数
    // formula: Math.pow(difficultyScale, elapsedSeconds / difficultyInterval)
    difficultyScale: 1.06,      // 每 10 秒异常效果变为 1.06x
    difficultyInterval: 10,     // 间隔秒数
  },

  /* ── 广告复活 ── */
  adRevive: {
    rollbackWindow: 30,          // 回滚到多少秒前的快照
    snapshotInterval: 10,        // 每 N 秒存一次快照
    maxSnapshots: 12,            // 最多保留快照数
  },

  /* ── 日志 ── */
  logs: {
    maxLines: 80,
    displayLines: 18,
  },

  /* ── 隐藏日志（广告解锁） ── */
  hiddenLogs: {
    maxUnlockedPerRun: 5,
  },

  /* ── 假结局 ── */
  fakeEnding: {
    consecutiveFailuresThreshold: 5,
    cooldownFailures: 3,
  },

  /* ── 发布模式 ──
     - false: 开发模式，广告失败也给奖励，方便本地测试
     - true:  发布模式，广告失败提示重试，不无条件发奖励
  */
  releaseMode: false,

  /* ── 模拟广告 ── */
  adContent: {
    adVideoDuration: 2000,
  },

  /* ── 广告位 ── */
  adUnits: {
    revive: 'adunit-xxxxx_revive',
    decode: 'adunit-xxxxx_decode',
    truth: 'adunit-xxxxx_truth',
  },
};

CONFIG;


// --- src/skins/elevator/skin.json ---
var __SKIN_DATA__ = {"meta":{"id":"elevator","name":"异常电梯控制台","subtitle":"MINIGAME · ANOMALY SYSTEM SIM"},"monitor":{"initial":"监控画面稳定：1 层轿厢内有 1 名乘客。","actions":{"openDoor":"监控：{floor} 层电梯门已打开。门外走廊光线异常。","closeDoor":"监控：轿厢门闭合。画面存在轻微拖影。","moveUp":"监控：电梯上行至 {floor} 层。乘客未看向摄像头。","moveDown":"监控：电梯下行至 {floor} 层。楼层指示灯短暂闪烁。","emergencyStop":"监控：电梯急停。轿厢灯光闪烁 3 次。","restartSystem":"监控：系统重启后恢复画面。部分录像帧丢失。"}},"actionLabels":{"openDoor":"开门","closeDoor":"关门","moveUp":"上行","moveDown":"下行","emergencyStop":"急停","restartSystem":"系统重启","inspectLog":"查看日志","unlockHiddenLog":"解码加密记录"},"doorLabels":{"open":"开启","closed":"关闭"},"directionLabels":{"up":"上行","down":"下行","idle":"待机"},"statusLabels":{"panelTitle":"电梯状态","floor":"楼层","door":"门状态","direction":"方向","passengers":"乘客","power":"电源","stability":"稳定度","anomalyLevel":"异常等级","reviveCount":"广告复活","adHintsCount":"加密解码","hiddenLogsCount":"待解码"},"canvasLabels":{"countdown":"值守倒计时","monitorPanel":"监控画面","actionPanel":"操作面板","logPanel":"系统日志","forceAnomaly":"触发异常测试","failureTitle":"系统崩溃","failureEyebrow":"SYSTEM FAILURE","monitorSignalStable":"SYSTEM: STABLE","monitorSignalUnstable":"SYSTEM: UNSTABLE","monitorSignalCorrupted":"SYSTEM: CORRUPTED","monitorThreat":"THREAT: {level}","failureMetricStability":"稳定度","failureMetricAnomaly":"异常","failureMetricRemaining":"剩余"},"actionFailMessages":{"openDoor_moving":"电梯移动中，禁止开门。","moveUp_doorNotClosed":"门未关闭，禁止移动。","moveDown_doorNotClosed":"门未关闭，禁止移动。","unknownAction":"未知操作：{actionId}","gameOver":"系统已崩溃，必须复活或重新开始。"},"actionFeedback":{"openDoor":"电梯门已打开。","closeDoor":"电梯门已关闭。","moveUp":"电梯开始上行。","moveDown":"电梯开始下行。","emergencyStop":"急停已执行。","emergencyStop_fail":"急停按钮失效。","restartSystem":"系统重启完成。","inspectLog":"已查看系统日志。","unlockHiddenLog_noLocked":"没有待解码的加密记录。","unlockHiddenLog_limit":"本局已解码 {count} 条记录，达到上限。"},"actionLogMessages":{"openDoor":"电梯门已在 {floor} 层打开。","closeDoor":"电梯门已关闭。","moveUp":"电梯开始上行，当前楼层 {floor}。","moveDown":"电梯开始下行，当前楼层 {floor}。","emergencyStop":"执行急停：移动已停止，稳定度下降。","emergencyStop_fail":"急停按钮无响应。异常等级上升。","restartSystem":"系统重启完成：异常等级下降，但消耗 {cost} 点电源。","inspectLog":"操作员查看系统日志：最近 30 秒存在未授权楼层请求。","inspectLog_hiddenRecords":"发现 {count} 条待解码加密记录。可观看模拟广告解锁完整内容。","unlockHiddenLog_ok":"模拟广告播放完成。加密记录已解码。"},"anomalies":[{"id":"phantom_floor","title":"不存在的楼层","severity":2,"monitor":"监控：电梯停在 13 层。建筑图纸中不存在该楼层。","adHint":"当楼层显示 13 时，不要开门，先执行系统重启。","effects":{"floor":13,"anomalyLevel":2,"stability":-10}},{"id":"camera_delay","title":"监控延迟","severity":1,"monitor":"监控：画面延迟 3 秒。乘客动作与控制台记录不同步。","adHint":"监控延迟时优先查看日志，不要连续移动。","effects":{"anomalyLevel":1,"stability":-6}},{"id":"zero_passenger_shadow","title":"门外有人但乘客数为 0","severity":2,"monitor":"监控：门外站着一个人，但乘客计数器显示 0。","adHint":"乘客数异常时保持关门，先急停再查日志。","effects":{"passengers":0,"anomalyLevel":2,"stability":-12}},{"id":"log_echo","title":"系统日志重复字符","severity":1,"monitor":"监控：系统日志开始重复输出“不要开门”。","adHint":"日志重复通常是轻度异常，系统重启可降低异常等级。","effects":{"anomalyLevel":1,"stability":-5}},{"id":"auto_button","title":"按钮自动亮起","severity":2,"monitor":"监控：没有乘客触碰按钮，B2 与 9 层按钮自动亮起。","adHint":"按钮自动亮起时不要跟随请求移动，先关门并急停。","effects":{"anomalyLevel":2,"power":-8}},{"id":"stop_failure","title":"急停按钮失效","severity":3,"monitor":"监控：急停按钮指示灯熄灭，控制台拒绝确认安全回路。","adHint":"急停失效时不要反复点击，优先系统重启。","effects":{"anomalyLevel":3,"stability":-15}},{"id":"negative_floor","title":"楼层显示为负数","severity":2,"monitor":"监控：楼层显示 -1。摄像头画面出现地下走廊。","adHint":"负数楼层不是正常地下层，立即重启系统。","effects":{"floor":-1,"anomalyLevel":2,"stability":-10}},{"id":"power_drain","title":"电源异常下降","severity":2,"monitor":"监控：备用电源自动接管，但电量仍在下降。","adHint":"电源异常下降时减少移动，优先关门与重启。","effects":{"anomalyLevel":2,"power":-22}},{"id":"door_refuse","title":"电梯门拒绝关闭","severity":2,"monitor":"监控：关门按钮已按下，门在合拢前自动弹开。异常状态持续。","adHint":"门拒绝关闭时不要连续按关门，先急停再重启系统。","effects":{"door":"open","anomalyLevel":2,"stability":-10}},{"id":"weight_mismatch","title":"载重数据异常","severity":1,"monitor":"监控：载重传感器读数 — 0kg。轿厢内有 1 名乘客。读数矛盾。","adHint":"载重异常时优先查日志，乘客数可能被重置。","effects":{"passengers":0,"anomalyLevel":1,"stability":-7}},{"id":"floor_jump","title":"楼层编号跳跃","severity":2,"monitor":"监控：电梯从 5 层直接移动到 9 层。摄像头画面缺失 4 帧。","adHint":"楼层跳跃时减少移动操作，用系统重启恢复楼层显示。","effects":{"floor":"+4","anomalyLevel":2,"stability":-12,"power":-10}},{"id":"emergency_lights","title":"应急灯异常启动","severity":3,"monitor":"监控：轿厢应急灯突然亮起。备用电源消耗加速。","adHint":"应急灯启动时尽量避免移动，立即重启系统可关闭应急灯。","effects":{"anomalyLevel":3,"stability":-14,"power":-20}}],"hiddenLogs":{"phantom_floor":{"title":"第13层施工记录","content":"2019年施工记录：第13层在竣工前被从建筑图纸中删除。\n原因：施工期间发生III级安全事件，3名工人失踪。\n楼层控制面板已被物理封堵，但系统仍能响应来自该层的按钮信号。"},"camera_delay":{"title":"监控系统校准记录","content":"校准日志 #4417：摄像头#03 与#07 存在 3 秒信号延迟。\n技术人员备注：延迟与第 13 层信号干扰有关，建议不要在 13 层停靠。"},"zero_passenger_shadow":{"title":"乘客记录异常说明","content":"传感器技术手册（节选）：\n红外传感器在非营业时段多次检测到热源信号，但乘客计数器持续归零。\n维修记录：传感器无故障。热源信号经比对——与员工体温档案不匹配。"},"log_echo":{"title":"日志系统诊断报告","content":"诊断报告 #FD-22-019：\n系统日志缓冲区检测到重复写入操作。重复内容「不要开门」的写入时间戳早于当前值班员登录时间。\n建议：检查前一值班员的退出状态。"},"auto_button":{"title":"控制系统审计追踪","content":"审计追踪 #AUD-882：\n自动按钮信号来源追溯至 5 号服务器（已于 2022 年停用）。\n该服务器的最后一条记录：「控制权移交程序未完成」。"},"stop_failure":{"title":"急停系统维护日志","content":"维护日志 #M-341：\n急停回路#2 在定期检查中被标记为「状态：不可用」。\n签署人签名无法识别。签署时间：3 年前。没有后续维修记录。"},"negative_floor":{"title":"地下层勘测报告","content":"建筑勘测报告（内部）：\n地下实际存在 4 层结构，但公开图纸仅标注 B1-B2。\nB3-B4 的电梯按钮在出厂时已被移除，但线路仍然通电。"},"power_drain":{"title":"备用电源异常报告","content":"异常报告 #P-877：\n备用电源在无负载状态下持续放电。经查，有一条非授权线路从备用电源柜分接至未知设备。\n线路标签：「不要切断」。"},"door_refuse":{"title":"门控系统事故报告","content":"事故报告 #D-1290：\n门控模块在连续 3 次异常重启后进入保护模式。\n模块日志输出最后一条：「识别到外部干扰信号。拒绝执行 — 保护乘员安全」。"},"weight_mismatch":{"title":"传感器校验记录","content":"校验记录 #W-554：\n载重传感器与红外传感器读数不一致。红外传感器在轿厢空载时检测到热源。\n技术人员备注：请确认值班员在操作前已清空轿厢。"},"floor_jump":{"title":"楼层定位日志","content":"定位日志 #F-213：\nGPS 楼层定位模块在校准前后记录的楼层编号不一致。\n系统自动修正失败。可能原因：参考信号源来自非标设备。"},"emergency_lights":{"title":"应急照明测试报告","content":"测试报告 #E-777：\n应急照明系统在无触发信号的情况下自行启动。\n供电线路检测到寄生回路。回路终端设备编号无法匹配任何已知设备清单。"}},"failure":{"summaries":{"power":"电源耗尽","stability":"稳定度归零","anomalyLevel":"异常等级失控","passengers":"乘客记录出现负数","default":"系统拒绝继续响应"},"defaultHint":"先关门，再重启系统，避免连续移动。","adHintPrefix":"广告提示：{hint}","adReviveRollback":"广告复活完成：回滚 {seconds} 秒，恢复至可控状态。","adReviveMonitor":"广告复活完成：回滚到 {seconds} 秒前的系统状态。","snapshotFallback":"可观看广告复活，回滚到 {seconds} 秒前的系统状态。","noSnapshotFallback":"可观看广告复活，回滚到初始系统状态。"},"fakeEnding":{"eyebrow":"⚠ SYSTEM ANOMALY DETECTED","title":"操作员关联异常","text":"系统检测到操作员第 {count} 次系统崩溃。\n根据《异常控制员守则》第 7 条，您已被标记为“异常关联人员”。\n前 {threshold} 次记录已被永久删除。\n建议您立即离开控制台并联系安保部门。","truthPlaceholder":"[???] 观看广告揭示真相。","truthContent":"这不是第一次，也不会是最后一次。\n这座建筑的异常系统从未被修复。\n每一任值班员最后都变成了「异常事件」本身。\n系统日志中关于「乘客」的记载——都是前任值班员的热源信号。\n你现在坐的位置，就是上一任值班员被发现的地方。"},"ui":{"viewAd":"观看广告复活","unlockAd":"解码加密记录","restart":"重新开始","revealTruth":"观看广告揭示真相","triggerTest":"触发异常测试","decodePrefix":"[解码记录]","initialLog":"异常电梯控制台已接管。等待操作员指令。","anomalyEventLog":"异常事件：{title}。{hint}","startTitle":"等待接管异常电梯","startCopy":"目标：值守 60 秒，观察监控、处理异常、避免系统崩溃。接管后倒计时才会启动。","startChecklist":"先读监控画面和系统日志\n异常出现时按提示执行操作\n失败后可通过模拟广告复活","startFailureRulesTitle":"失败条件","startFailureRules":"电源归零\n稳定度归零\n异常等级失控","startButton":"开始接管","successfulShift":"本轮值守结束。系统仍未解释全部异常。","shiftComplete":"值守完成。连续失败计数已重置。","hiddenLogCaptured":"加密记录已捕获：{title}。使用「查看日志」功能解码。","unlockResult":"已解码：{title}","decodeMonitor":"解码完成：{title}。完整内容已写入系统日志。"}};

// --- src/skinManager.js ---
/**
 * skinManager.js — 换皮系统核心
 *
 * 负责加载皮肤 JSON 并提供模板字符串替换 (t函数)。
 * 所有游戏内容文本集中管理，实现换皮 = 换 JSON。
 *
 * 用法：
 *   import { t, anom, loadSkin } from './skinManager.js';
 *   t('meta.name');                      // "异常电梯控制台"
 *   t('actionLabels.openDoor');           // "开门"
 *   t('monitor.actions.moveUp', { floor: 5 }); // 带模板参数
 *   anom('phantom_floor').title;          // 获取异常事件数据
 */


let currentSkin = __SKIN_DATA__;

/**
 * 加载指定皮肤数据
 * @param {object} skinData — 皮肤 JSON 对象
 */
function loadSkin(skinData) {
  currentSkin = skinData;
}

/** 获取当前皮肤对象 */
function getSkin() {
  return currentSkin;
}

/**
 * 根据点分 key 获取皮肤文本，支持 {param} 模板替换
 * @param {string} key — 如 'meta.name'、'actionLabels.openDoor'
 * @param {object} params — 可选模板参数
 * @returns {string}
 */
function t(key, params = {}) {
  const value = key.split('.').reduce((o, k) => (o != null ? o[k] : undefined), currentSkin);
  if (value === undefined || value === null) {
    console.warn(`[skinManager] missing key: ${key}`);
    return `{${key}}`;
  }
  if (typeof value === 'string') {
    return value.replace(/\{(\w+)\}/g, (_, k) => params[k] ?? `{${k}}`);
  }
  return value;
}

/**
 * 获取所有异常事件定义（来自皮肤）
 * @returns {Array<{id, title, severity, monitor, adHint, effects}>}
 */
function getAnomalies() {
  return currentSkin.anomalies || [];
}

/**
 * 按 ID 获取单个异常定义
 */
function getAnomaly(id) {
  return (currentSkin.anomalies || []).find(a => a.id === id) || null;
}

/**
 * 获取异常关联的隐藏日志
 */
function getHiddenLog(anomalyId) {
  return currentSkin.hiddenLogs?.[anomalyId] || null;
}

/**
 * 创建异常事件的 effects 应用到 state 上
 * @param {object} state — 当前游戏状态
 * @param {object} effects — 来自皮肤的 effects 对象
 * @returns {object} 新的 state
 */
function applyEffects(state, effects) {
  const next = { ...state };
  for (const [field, value] of Object.entries(effects || {})) {
    if (typeof value === 'number') {
      next[field] = (next[field] ?? 0) + value;
    } else if (typeof value === 'string' && value.startsWith('+')) {
      next[field] = (next[field] ?? 0) + parseInt(value, 10);
    } else {
      // 直接赋值（如 door: 'open', floor: 13）
      next[field] = value;
    }
  }
  return next;
}

/**
 * 获取操作反馈文本
 */
function actionText(actionId, key, params = {}) {
  return t(`action${key}.${actionId}`, params);
}

/**
 * 获取操作标签文本
 */
function actionLabel(actionId, count) {
  const label = t(`actionLabels.${actionId}`);
  if (count !== undefined) return `${label} (${count})`;
  return label;
}


// --- src/rollback.js ---

function findRollbackSnapshot(snapshots, elapsed) {
  if (!snapshots || snapshots.length === 0) return null;
  const targetElapsed = Math.max(0, elapsed - CONFIG.adRevive.rollbackWindow);
  let best = snapshots[0];
  let bestDist = Math.abs(best.at - targetElapsed);
  for (const snap of snapshots) {
    const dist = Math.abs(snap.at - targetElapsed);
    if (dist < bestDist) {
      bestDist = dist;
      best = snap;
    }
  }
  return best;
}


// --- src/feedback.js ---


function classifyFeedbackPriority(type) {
  if (type === 'danger') return 'high';
  if (type === 'ad') return 'special';
  if (type === 'success') return 'success';
  if (type === 'warn') return 'medium';
  return 'normal';
}

function createFeedbackLine(type, message, time = 0) {
  const safeTime = Math.max(0, Math.floor(time));
  const minutes = String(Math.floor(safeTime / 60)).padStart(2, '0');
  const seconds = String(safeTime % 60).padStart(2, '0');
  return {
    type,
    priority: classifyFeedbackPriority(type),
    time: safeTime,
    text: `[${minutes}:${seconds}] ${message}`,
  };
}

function summarizeFailure(state) {
  const reasons = [];
  const s = state;
  if (s.power <= 0) reasons.push(t('failure.summaries.power'));
  if (s.stability <= 0) reasons.push(t('failure.summaries.stability'));
  if (s.anomalyLevel >= 6) reasons.push(t('failure.summaries.anomalyLevel'));
  if (s.passengers < 0) reasons.push(t('failure.summaries.passengers'));
  if (reasons.length === 0) reasons.push(t('failure.summaries.default'));

  const snapshots = s.snapshots || [];
  let rollbackSec = 0;
  if (snapshots.length > 0) {
    const best = findRollbackSnapshot(snapshots, s.elapsed);
    rollbackSec = s.elapsed - best.at;
  }

  if (snapshots.length > 0) {
    return `${reasons.join('、')}。${t('failure.snapshotFallback', { seconds: rollbackSec })}`;
  }
  return `${reasons.join('、')}。${t('failure.noSnapshotFallback')}`;
}

function getToneForState(state) {
  if (state.gameOver) return 'danger';
  if (state.anomalyLevel >= 4 || state.stability < 35) return 'critical';
  if (state.anomalyLevel >= 2 || state.power < 45) return 'warn';
  return 'normal';
}


// --- src/state.js ---




function createInitialState() {
  const c = CONFIG.initial;
  return {
    floor: c.floor,
    door: c.door,
    moving: c.moving,
    direction: c.direction,
    power: c.power,
    stability: c.stability,
    anomalyLevel: c.anomalyLevel,
    passengers: c.passengers,
    gameOver: c.gameOver,
    elapsed: 0,
    remaining: c.duration,
    adRevivesUsed: 0,
    hiddenLogsUnlocked: 0,
    lastAdHint: '',
    monitor: t('monitor.initial'),
    activeAnomaly: null,
    snapshots: [],
    hiddenLogs: [],
    adHintsUsed: 0,
    consecutiveFailures: 0,
    fakeEndingCount: 0,
    fakeEndingCooldownRemaining: 0,
    fakeEndingTriggered: false,
    fakeEndingUnlocked: false,
    // 复盘统计（局内累积）
    anomaliesTriggeredTotal: 0,
    maxAnomalySeverity: 0,
    logs: [createFeedbackLine('info', t('ui.initialLog'), 0)],
  };
}

function cloneState(state) {
  return structuredClone(state);
}

function appendLog(state, type, message) {
  const next = cloneState(state);
  next.logs.push(createFeedbackLine(type, message, next.elapsed ?? 0));
  if (next.logs.length > CONFIG.logs.maxLines) next.logs = next.logs.slice(-CONFIG.logs.maxLines);
  return next;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function checkFailure(state) {
  const next = cloneState(state);
  const f = CONFIG.failure;
  if (next.power <= f.powerMin || next.stability <= f.stabilityMin || next.anomalyLevel >= f.anomalyLevelMax || next.passengers < f.passengersMin) {
    next.gameOver = true;
    next.moving = false;
    next.direction = 'idle';
  }
  return next;
}

function saveSnapshot(state) {
  const snapshots = [...(state.snapshots || [])];
  // Build a clean copy of the state without the snapshots array (no nesting)
  const clean = {};
  for (const key of Object.keys(state)) {
    if (key === 'snapshots') continue;
    clean[key] = structuredClone(state[key]);
  }
  snapshots.push({ at: state.elapsed, state: clean });
  const next = cloneState(state);
  next.snapshots = snapshots.slice(-CONFIG.adRevive.maxSnapshots);
  return next;
}


function reviveFromAd(state) {
  const snapshots = state.snapshots || [];
  const best = findRollbackSnapshot(snapshots, state.elapsed);

  let next;
  if (best) {
    next = cloneState(best.state);
    next.snapshots = snapshots; // preserve snapshot history
    next.rollbackSeconds = state.elapsed - best.at;
  } else {
    // No snapshot early enough — fall back to initial baseline
    next = createInitialState();
    next.snapshots = snapshots;
    next.rollbackSeconds = state.elapsed;
    next.elapsed = state.elapsed; // keep the clock running
    next.remaining = Math.max(1, state.remaining);
  }

  next.gameOver = false;
  next.door = 'closed';
  next.moving = false;
  next.direction = 'idle';
  next.activeAnomaly = null;
  next.adRevivesUsed += 1;
  next.monitor = t('failure.adReviveMonitor', { seconds: next.rollbackSeconds });
  next = appendLog(next, 'ad', t('failure.adReviveRollback', { seconds: next.rollbackSeconds }));
  return next;
}

function tickState(state, seconds = 1) {
  let next = cloneState(state);
  const tk = CONFIG.tick;
  next.elapsed += seconds;
  next.remaining = clamp(next.remaining - seconds, 0, CONFIG.initial.duration);
  if (next.moving) {
    next.power = clamp(next.power - seconds * tk.powerDrainMoving, 0, 100);
    next.stability = clamp(next.stability - seconds * tk.stabilityDrainMoving, 0, 100);
  } else {
    next.power = clamp(next.power - seconds * tk.powerDrainIdle, 0, 100);
  }
  if (next.remaining <= 0) {
    next.gameOver = true;
    next = appendLog(next, 'success', t('ui.successfulShift'));
  }
  return checkFailure(next);
}

function recordSuccessfulShift(state) {
  let next = cloneState(state);
  next.consecutiveFailures = 0;
  next.fakeEndingCooldownRemaining = 0;
  next.fakeEndingTriggered = false;
  next.fakeEndingUnlocked = false;
  next.fakeEndingCount = 0;
  next = appendLog(next, 'success', t('ui.shiftComplete'));
  return next;
}

function recordFailure(state) {
  const fe = CONFIG.fakeEnding;
  const next = cloneState(state);
  next.consecutiveFailures += 1;

  if (next.fakeEndingCooldownRemaining > 0) {
    next.fakeEndingCooldownRemaining -= 1;
    next.fakeEndingTriggered = false;
    return next;
  }

  if (next.consecutiveFailures >= fe.consecutiveFailuresThreshold) {
    next.fakeEndingTriggered = true;
    next.fakeEndingUnlocked = false;
    next.fakeEndingCount = next.consecutiveFailures;
    next.consecutiveFailures = 0;
    next.fakeEndingCooldownRemaining = fe.cooldownFailures;
  }

  return next;
}


// --- src/events.js ---



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
    effects: skinDef.effects || {},
    apply(state) {
      const next = cloneState(state);
      const effects = skinDef.effects || {};
      // 计算难度倍率
      const elapsed = state.elapsed || 0;
      const diffScale = CONFIG.anomaly.difficultyScale || 1;
      const diffInterval = CONFIG.anomaly.difficultyInterval || 10;
      const multiplier = Math.pow(diffScale, elapsed / diffInterval);

      for (const [field, value] of Object.entries(effects)) {
        let adjusted = value;
        // 负数效果（消耗类）才乘难度系数
        if (typeof value === 'number' && value < 0) {
          adjusted = Math.round(value * multiplier);
        } else if (typeof value === 'string' && isDeltaEffect(value) && parseInt(value, 10) < 0) {
          const num = parseInt(value, 10);
          adjusted = `${Math.round(num * multiplier)}`;
        }
        if (typeof adjusted === 'number' && shouldAddNumericEffect(field, adjusted)) {
          next[field] = clamp((next[field] ?? 0) + adjusted, 0, 100);
        } else if (typeof adjusted === 'string' && isDeltaEffect(adjusted)) {
          next[field] = Math.min(CONFIG.bounds.maxFloor, (next[field] ?? 0) + parseInt(adjusted, 10));
        } else {
          next[field] = adjusted;
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

function isDeltaEffect(value) {
  return /^[+-]\d+$/.test(value);
}

function shouldAddNumericEffect(field, value) {
  if (value < 0) return true;
  return field === 'power' || field === 'stability' || field === 'anomalyLevel';
}

/** 当前皮肤生成的异常事件列表 */
const ANOMALIES = getAnomalies().map(createAnomaly);

function findAnomaly(id) {
  return ANOMALIES.find((event) => event.id === id);
}

function applyAnomaly(state, id) {
  const event = findAnomaly(id);
  if (!event) throw new Error(`Unknown anomaly: ${id}`);
  let next = event.apply(state);
  next.lastAdHint = event.adHint;
  // 复盘统计
  next.anomaliesTriggeredTotal = (next.anomaliesTriggeredTotal ?? 0) + 1;
  next.maxAnomalySeverity = Math.max(next.maxAnomalySeverity ?? 0, event.severity);
  // 添加关联隐藏日志（不重复）
  const raw = getHiddenLog(id);
  if (raw && !next.hiddenLogs.some(h => h.id === id + '_log')) {
    next.hiddenLogs.push({ id: id + '_log', title: raw.title, content: raw.content, locked: true });
    next = appendLog(next, 'info', t('ui.hiddenLogCaptured', { title: raw.title }));
  }
  next = appendLog(next, event.severity >= 3 ? 'danger' : 'warn', t('ui.anomalyEventLog', {
    title: event.title,
    hint: event.adHint,
  }));
  return { event, state: checkFailure(next) };
}

function pickNextAnomaly(state, random = Math.random) {
  const pressure = Math.min(ANOMALIES.length - 1, Math.floor(state.anomalyLevel / CONFIG.anomaly.pressureDivisor));
  const index = Math.min(ANOMALIES.length - 1, Math.floor(random() * ANOMALIES.length + pressure) % ANOMALIES.length);
  return ANOMALIES[index];
}
/** @deprecated 请使用 getHiddenLog() 代替 */
const _buildHiddenLogsMap = () => {
  const map = {};
  const anomalies = getAnomalies();
  for (const a of anomalies) {
    const hl = getHiddenLog(a.id);
    if (hl) {
      map[a.id] = { id: `${a.id}_log`, title: hl.title, content: hl.content };
    }
  }
  return map;
};

const HIDDEN_LOGS = _buildHiddenLogsMap();


// --- src/actions.js ---



const ACTIONS = {
  openDoor(state) {
    if (state.moving) return fail(state, t('actionFailMessages.openDoor_moving'));
    let next = cloneState(state);
    next.door = 'open';
    next.monitor = t('monitor.actions.openDoor', { floor: next.floor });
    next = appendLog(next, 'info', t('actionLogMessages.openDoor', { floor: next.floor }));
    return ok(next, t('actionFeedback.openDoor'));
  },

  closeDoor(state) {
    let next = cloneState(state);
    next.door = 'closed';
    next.monitor = t('monitor.actions.closeDoor');
    next = appendLog(next, 'info', t('actionLogMessages.closeDoor'));
    return ok(next, t('actionFeedback.closeDoor'));
  },

  moveUp(state) {
    if (state.door !== 'closed') return fail(state, t('actionFailMessages.moveUp_doorNotClosed'));
    let next = cloneState(state);
    const a = CONFIG.actions.moveUp;
    next.floor += 1;
    next.moving = true;
    next.direction = 'up';
    next.power = clamp(next.power - a.powerCost, 0, 100);
    next.stability = clamp(next.stability - a.stabilityCost, 0, 100);
    next.monitor = t('monitor.actions.moveUp', { floor: next.floor });
    next = appendLog(next, 'info', t('actionLogMessages.moveUp', { floor: next.floor }));
    return ok(checkFailure(next), t('actionFeedback.moveUp'));
  },

  moveDown(state) {
    if (state.door !== 'closed') return fail(state, t('actionFailMessages.moveDown_doorNotClosed'));
    let next = cloneState(state);
    const a = CONFIG.actions.moveDown;
    next.floor -= 1;
    next.moving = true;
    next.direction = 'down';
    next.power = clamp(next.power - a.powerCost, 0, 100);
    next.stability = clamp(next.stability - a.stabilityCost, 0, 100);
    next.monitor = t('monitor.actions.moveDown', { floor: next.floor });
    next = appendLog(next, 'info', t('actionLogMessages.moveDown', { floor: next.floor }));
    return ok(checkFailure(next), t('actionFeedback.moveDown'));
  },

  emergencyStop(state) {
    let next = cloneState(state);
    const es = CONFIG.actions.emergencyStop;
    if (next.activeAnomaly === 'stop_failure') {
      next.anomalyLevel = clamp(next.anomalyLevel + 1, 0, 6);
      next.stability = clamp(next.stability - es.stabilityCostOnFailure, 0, 100);
      next = appendLog(next, 'danger', t('actionLogMessages.emergencyStop_fail'));
      return fail(checkFailure(next), t('actionFeedback.emergencyStop_fail'));
    }
    next.moving = false;
    next.direction = 'idle';
    next.stability = clamp(next.stability - es.stabilityCost, 0, 100);
    next.monitor = t('monitor.actions.emergencyStop');
    next = appendLog(next, 'warn', t('actionLogMessages.emergencyStop'));
    return ok(checkFailure(next), t('actionFeedback.emergencyStop'));
  },

  restartSystem(state) {
    let next = cloneState(state);
    const rs = CONFIG.actions.restartSystem;
    next.anomalyLevel = Math.max(0, next.anomalyLevel - rs.anomalyLevelReduce);
    next.stability = clamp(next.stability + rs.stabilityRestore, 0, 100);
    next.power = clamp(next.power - rs.powerCost, 0, 100);
    next.moving = false;
    next.direction = 'idle';
    next.activeAnomaly = null;
    next.monitor = t('monitor.actions.restartSystem');
    next = appendLog(next, 'warn', t('actionLogMessages.restartSystem', { cost: rs.powerCost }));
    return ok(checkFailure(next), t('actionFeedback.restartSystem'));
  },

  inspectLog(state) {
    let next = appendLog(state, 'info', t('actionLogMessages.inspectLog'));
    const lockedCount = next.hiddenLogs.filter(h => h.locked).length;
    if (lockedCount > 0) {
      next = appendLog(next, 'ad', t('actionLogMessages.inspectLog_hiddenRecords', { count: lockedCount }));
    }
    return ok(next, t('actionFeedback.inspectLog'));
  },

  unlockHiddenLog(state) {
    // 找到第一条仍锁定的隐藏日志
    const locked = state.hiddenLogs.find(h => h.locked);
    if (!locked) {
      return fail(state, t('actionFeedback.unlockHiddenLog_noLocked'));
    }
    const unlocked = state.adHintsUsed;
    if (unlocked >= CONFIG.hiddenLogs.maxUnlockedPerRun) {
      return fail(state, t('actionFeedback.unlockHiddenLog_limit', { count: unlocked }));
    }
    let next = cloneState(state);
    const idx = next.hiddenLogs.findIndex(h => h.id === locked.id);
    if (idx !== -1) {
      next.hiddenLogs[idx] = { ...next.hiddenLogs[idx], locked: false };
    }
    next.adHintsUsed += 1;
    next = appendLog(next, 'ad', t('actionLogMessages.unlockHiddenLog_ok'));
    next.monitor = t('ui.decodeMonitor', { title: locked.title });
    return ok(next, t('ui.unlockResult', { title: locked.title }));
  },
};

function ok(state, message) {
  return { ok: true, state, message };
}

function fail(state, message) {
  const next = appendLog(state, 'warn', message);
  return { ok: false, state: next, message };
}

function performAction(state, actionId) {
  const action = ACTIONS[actionId];
  if (!action) return fail(state, t('actionFailMessages.unknownAction', { actionId }));
  if (state.gameOver && actionId !== 'inspectLog') return fail(state, t('actionFailMessages.gameOver'));
  return action(state);
}

const ACTION_IDS = [
  'openDoor',
  'closeDoor',
  'moveUp',
  'moveDown',
  'emergencyStop',
  'restartSystem',
  'inspectLog',
  'unlockHiddenLog',
];

function getAvailableActions() {
  return ACTION_IDS.map(id => ({ id, label: actionLabel(id) }));
}


// --- src/uiLabels.js ---

function getDomLabels() {
  const skin = getSkin();
  const status = skin.statusLabels || {};
  const canvas = skin.canvasLabels || {};

  return {
    countdown: canvas.countdown || '值守倒计时',
    statusPanel: status.panelTitle || '电梯状态',
    monitorPanel: canvas.monitorPanel || '监控画面',
    actionPanel: canvas.actionPanel || '操作面板',
    logPanel: canvas.logPanel || '系统日志',
    forceAnomaly: canvas.forceAnomaly || t('ui.triggerTest'),
    failureTitle: canvas.failureTitle || '系统崩溃',
    failureEyebrow: canvas.failureEyebrow || 'SYSTEM FAILURE',
    monitorSignal: {
      stable: canvas.monitorSignalStable || 'SIGNAL: STABLE',
      unstable: canvas.monitorSignalUnstable || 'SIGNAL: UNSTABLE',
      corrupted: canvas.monitorSignalCorrupted || 'SIGNAL: CORRUPTED',
    },
    monitorThreat: (level) => (canvas.monitorThreat || 'THREAT: {level}').replace('{level}', level),
    failureMetrics: [
      { key: 'power', label: status.power || '电源' },
      { key: 'stability', label: canvas.failureMetricStability || status.stability || '稳定度' },
      { key: 'anomalyLevel', label: canvas.failureMetricAnomaly || status.anomalyLevel || '异常' },
      { key: 'remaining', label: canvas.failureMetricRemaining || '剩余' },
    ],
    revive: t('ui.viewAd'),
    restart: t('ui.restart'),
    revealTruth: t('ui.revealTruth'),
    start: {
      title: t('ui.startTitle'),
      copy: t('ui.startCopy'),
      checklist: t('ui.startChecklist').split('\n').filter(Boolean),
      failureRulesTitle: t('ui.startFailureRulesTitle'),
      failureRules: t('ui.startFailureRules').split('\n').filter(Boolean),
      button: t('ui.startButton'),
    },
    status: {
      floor: status.floor || '楼层',
      door: status.door || '门状态',
      direction: status.direction || '方向',
      passengers: status.passengers || '乘客',
      power: status.power || '电源',
      stability: status.stability || '稳定度',
      anomalyLevel: status.anomalyLevel || '异常等级',
      reviveCount: status.reviveCount || '广告复活',
      adHintsCount: status.adHintsCount || '加密解码',
      hiddenLogsCount: status.hiddenLogsCount || '待解码',
    },
  };
}

function getDecodedMonitorText(hiddenLog) {
  return `${t('ui.decodePrefix')} ${hiddenLog.title}\n${hiddenLog.content}`;
}

function getDoorLabel(value) {
  const labels = getSkin().doorLabels || { open: '开启', closed: '关闭' };
  return labels[value] || value;
}

function getDirectionLabel(value) {
  const labels = getSkin().directionLabels || { up: '上行', down: '下行', idle: '待机' };
  return labels[value] || value;
}


// --- src/runtimeSession.js ---


function createRuntimeSession() {
  return {
    state: createInitialState(),
    nextAnomalyAt: CONFIG.anomaly.firstTriggerAt,
  };
}

function restartRuntimeSession() {
  return createRuntimeSession();
}

function scheduleNextAnomalyAfterTrigger(elapsed, random = Math.random) {
  const cd = CONFIG.anomaly;
  const span = cd.cooldownMax - cd.cooldownMin + 1;
  return elapsed + cd.cooldownMin + Math.floor(random() * span);
}

function scheduleNextAnomalyAfterRevive(elapsed) {
  return elapsed + CONFIG.anomaly.cooldownMin;
}


// --- platform/canvasRenderer.js ---
/**
 * canvasRenderer.js — Canvas 渲染器
 *
 * 完全替代 index.html + styles.css 的 DOM 渲染。
 * 在小游戏平台（微信/抖音）上使用 Canvas 渲染，
 * 在浏览器中也可作为独立渲染模式。
 *
 * 设计宽度：750px（标准移动端设计尺寸）
 */





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

function getCanvasStaticLabels() {
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

function getCanvasFailureOverlayCopy(state) {
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

function getCanvasStatusItems(state) {
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

function getCanvasMeterBars(state) {
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

function getCanvasActionButtons(state) {
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

function onCanvasClick(x, y, state, callbacks) {
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
function render(state) {
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
function init(canvasEl) {
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


// --- platform/miniGameRuntime.js ---
/**
 * miniGameRuntime.js — 微信/抖音小游戏 Canvas 运行时入口
 *
 * 不依赖 DOM/window。只使用小游戏全局 API（wx/tt）或标准全局函数。
 */




function getHostApi() {
  if (typeof wx !== 'undefined' && wx) return wx;
  if (typeof tt !== 'undefined' && tt) return tt;
  return null;
}

function getNow() {
  return Date.now();
}

function nextFrame(api, callback) {
  if (api && typeof api.requestAnimationFrame === 'function') {
    return api.requestAnimationFrame(callback);
  }
  if (typeof requestAnimationFrame === 'function') {
    return requestAnimationFrame(callback);
  }
  return setTimeout(callback, 16);
}

function getSystemInfo(api) {
  if (api && typeof api.getSystemInfoSync === 'function') {
    return api.getSystemInfoSync();
  }
  return { windowWidth: 750, windowHeight: 1334, pixelRatio: 1 };
}

function createRewardedAd(api, adUnitId, onReward) {
  if (!api || typeof api.createRewardedVideoAd !== 'function' || !adUnitId) {
    return () => Promise.resolve().then(onReward);
  }

  const ad = api.createRewardedVideoAd({ adUnitId });
  let granted = false;
  ad.onClose?.((res) => {
    if (res && res.isEnded && !granted) {
      granted = true;
      onReward?.();
    }
  });
  ad.onError?.(() => {
    if (!granted) {
      granted = true;
      onReward?.();
    }
  });

  return () => ad.show()
    .catch(() => ad.load?.().then(() => ad.show()))
    .catch(() => {
      if (!granted) {
        granted = true;
        onReward?.();
      }
    });
}

function startMiniGame() {
  const api = getHostApi();
  if (!api || typeof api.createCanvas !== 'function') {
    throw new Error('[MINIGAME] mini-game runtime requires wx.createCanvas() or tt.createCanvas()');
  }

  const canvas = api.createCanvas();
  const info = getSystemInfo(api);
  const dims = initCanvasRenderer(canvas);
  let session = createRuntimeSession();
  let state = session.state;
  let nextAnomalyAt = session.nextAnomalyAt;
  let lastTickAt = getNow();
  let lastSnapshotAt = 0;
  let failureRecorded = false;

  const reviveAd = createRewardedAd(api, CONFIG.adUnits?.revive, () => {
    state = reviveFromAd(state);
    nextAnomalyAt = scheduleNextAnomalyAfterRevive(state.elapsed);
    failureRecorded = false;
  });

  const truthAd = createRewardedAd(api, CONFIG.adUnits?.truth, () => {
    state = { ...state, fakeEndingUnlocked: true, fakeEndingTruth: state.lastAdHint || '' };
  });

  function restart() {
    session = createRuntimeSession();
    state = session.state;
    nextAnomalyAt = session.nextAnomalyAt;
    lastSnapshotAt = 0;
    failureRecorded = false;
  }

  function forceAnomaly() {
    if (state.gameOver) return;
    const event = pickNextAnomaly(state);
    const result = applyAnomaly(state, event.id);
    state = result.state;
    nextAnomalyAt = scheduleNextAnomalyAfterTrigger(state.elapsed);
  }

  function handleAction(actionId) {
    if (state.gameOver) return;
    const result = performAction(state, actionId);
    state = result.state;
  }

  function handleAd(kind) {
    if (kind === 'truth') {
      truthAd();
    } else {
      reviveAd();
    }
  }

  function onTouch(e) {
    const touch = e.touches?.[0] || e.changedTouches?.[0] || e;
    const screenW = info.windowWidth || 750;
    const screenH = info.windowHeight || 1334;
    const x = (touch.clientX ?? touch.x ?? 0) * (750 / screenW);
    const y = (touch.clientY ?? touch.y ?? 0) * (dims.height / screenH);
    onCanvasClick(x, y, state, {
      onAction: handleAction,
      onForceAnomaly: forceAnomaly,
      onAdRevive: handleAd,
      onRestart: restart,
    });
  }

  api.onTouchStart?.(onTouch);

  function update() {
    const now = getNow();
    const delta = Math.floor((now - lastTickAt) / 1000);
    if (delta > 0) {
      lastTickAt += delta * 1000;
      if (!state.gameOver) {
        for (let i = 0; i < delta; i += 1) {
          state = tickState(state, 1);
          if (!state.gameOver && state.elapsed - lastSnapshotAt >= CONFIG.adRevive.snapshotInterval) {
            state = saveSnapshot(state);
            lastSnapshotAt = state.elapsed;
          }
          if (!state.gameOver && state.elapsed >= nextAnomalyAt) {
            const event = pickNextAnomaly(state);
            const result = applyAnomaly(state, event.id);
            state = result.state;
            nextAnomalyAt = scheduleNextAnomalyAfterTrigger(state.elapsed);
          }
        }
      }
      if (state.gameOver && !failureRecorded) {
        state = state.remaining <= 0 ? recordSuccessfulShift(state) : recordFailure(state);
        failureRecorded = true;
      }
    }

    render(state);
    nextFrame(api, update);
  }

  render(state);
  nextFrame(api, update);
  return { canvas, getState: () => state, restart };
}



// ── 平台入口 ──
startMiniGame();
})();

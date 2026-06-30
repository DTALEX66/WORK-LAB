/**
 * gameConfig.js — MINIGAME 平衡参数配置（单一配置源）
 *
 * 所有游戏平衡参数集中于此，便于调优和后续换皮。
 * 换皮时只需修改此文件即可改变游戏难度/节奏。
 *
 * 用法：
 *   import CONFIG from './gameConfig.js';
 *   CONFIG.tick.powerDrainMoving  // 0.7
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
    powerDrainMoving: 0.7,    // 移动中每秒电源消耗
    powerDrainIdle: 0.18,     // 待机每秒电源消耗
    stabilityDrainMoving: 0.25, // 移动中每秒稳定度消耗
  },

  /* ── 操作消耗/效果 ── */
  actions: {
    moveUp: {
      powerCost: 6,
      stabilityCost: 2,
    },
    moveDown: {
      powerCost: 6,
      stabilityCost: 2,
    },
    emergencyStop: {
      stabilityCost: 6,
      stabilityCostOnFailure: 16, // 急停失效时的额外惩罚
    },
    restartSystem: {
      anomalyLevelReduce: 2,
      stabilityRestore: 15,
      powerCost: 10,
    },
  },

  /* ── 失败条件 ── */
  failure: {
    powerMin: 0,
    stabilityMin: 0,
    anomalyLevelMax: 6,
    passengersMin: 0,
  },

  /* ── 异常系统 ── */
  anomaly: {
    firstTriggerAt: 12,         // 首次异常触发时间（秒）
    cooldownMin: 8,             // 异常后最短冷却
    cooldownMax: 13,            // 异常后最长冷却
    pressureDivisor: 2,         // pickNextAnomaly 压力算法分母
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
    unlockLogMessage: '模拟广告播放完成。加密记录已解码。',
  },

  /* ── 假结局 ── */
  fakeEnding: {
    consecutiveFailuresThreshold: 5,
    cooldownFailures: 3,
  },

  /* ── 模拟广告 ── */
  adContent: {
    adVideoDuration: 2000,
  },
};

export default CONFIG;

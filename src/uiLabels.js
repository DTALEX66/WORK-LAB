import { getSkin, t } from './skinManager.js';

export function getDomLabels() {
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
    revive: t('ui.viewAd'),
    restart: t('ui.restart'),
    revealTruth: t('ui.revealTruth'),
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

export function getDecodedMonitorText(hiddenLog) {
  return `${t('ui.decodePrefix')} ${hiddenLog.title}\n${hiddenLog.content}`;
}

export function getOperatorCue(state, nextAnomalyAt, recommendedActionLabel = null) {
  const elapsed = Math.max(0, Math.floor(state?.elapsed ?? 0));
  const firstAnomalySeen = (state?.anomaliesTriggeredTotal ?? 0) > 0;

  if (state?.gameOver) {
    return 'DEBRIEF: 先看崩溃原因；广告复活会回滚到可控状态。';
  }

  if (state?.activeAnomaly) {
    const action = recommendedActionLabel ? ` 执行：${recommendedActionLabel}` : '';
    return `CUE: CCTV/日志先读；黄色描边是推荐按键。${action}`;
  }

  if (!firstAnomalySeen) {
    const seconds = Math.max(0, Math.ceil((nextAnomalyAt ?? elapsed) - elapsed));
    return `STANDBY: 首个异常 ${seconds}s 内出现；盯住 CCTV。`;
  }

  return 'CUE: 异常升高先看日志；危险态优先重启。';
}

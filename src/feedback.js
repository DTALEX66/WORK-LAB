export function createFeedbackLine(type, message, time = 0) {
  const safeTime = Math.max(0, Math.floor(time));
  const minutes = String(Math.floor(safeTime / 60)).padStart(2, '0');
  const seconds = String(safeTime % 60).padStart(2, '0');
  return {
    type,
    time: safeTime,
    text: `[${minutes}:${seconds}] ${message}`,
  };
}

export function summarizeFailure(state) {
  const reasons = [];
  if (state.power <= 0) reasons.push('电源耗尽');
  if (state.stability <= 0) reasons.push('稳定度归零');
  if (state.anomalyLevel >= 6) reasons.push('异常等级失控');
  if (state.passengers < 0) reasons.push('乘客记录出现负数');
  if (reasons.length === 0) reasons.push('系统拒绝继续响应');

  // Compute actual rollback time from snapshots
  const snapshots = state.snapshots || [];
  const targetElapsed = Math.max(0, state.elapsed - 30);
  let rollbackSec = 0;
  if (snapshots.length > 0) {
    let best = snapshots[0];
    let bestDist = Math.abs(best.at - targetElapsed);
    for (const snap of snapshots) {
      const dist = Math.abs(snap.at - targetElapsed);
      if (dist < bestDist) { bestDist = dist; best = snap; }
    }
    rollbackSec = state.elapsed - best.at;
  }

  if (snapshots.length > 0) {
    return `${reasons.join('、')}。可观看广告复活，回滚到 ${rollbackSec} 秒前的系统状态。`;
  }
  return `${reasons.join('、')}。可观看广告复活，回滚到初始系统状态。`;
}

export function getToneForState(state) {
  if (state.gameOver) return 'danger';
  if (state.anomalyLevel >= 4 || state.stability < 35) return 'critical';
  if (state.anomalyLevel >= 2 || state.power < 45) return 'warn';
  return 'normal';
}

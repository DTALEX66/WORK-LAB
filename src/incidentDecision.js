import { appendLog, checkFailure, clamp, cloneState } from './state.js';
import { t } from './skinManager.js';

export function openInspection(state, options) {
  const duration = Math.max(3, Math.floor(options.duration ?? 7));
  let next = cloneState(state);
  next.inspection = {
    id: options.id,
    kind: options.kind === 'anomaly' ? 'anomaly' : 'normal',
    title: options.title,
    openedAt: next.elapsed ?? 0,
    expiresAt: (next.elapsed ?? 0) + duration,
    status: 'pending',
    choice: null,
  };
  next = appendLog(next, 'info', t('ui.inspectionPrompt', {
    title: options.title,
    seconds: duration,
  }));
  return next;
}

export function submitInspection(state, choice) {
  const inspection = state.inspection;
  if (!inspection || inspection.status !== 'pending') {
    return { state, accepted: false, correct: false };
  }

  let next = cloneState(state);
  const normalizedChoice = choice === 'anomaly' ? 'anomaly' : 'normal';
  const correct = normalizedChoice === inspection.kind;
  next.inspection = {
    ...inspection,
    status: 'resolved',
    choice: normalizedChoice,
    correct,
    resolvedAt: next.elapsed ?? 0,
  };
  next.decisionsCorrect = (next.decisionsCorrect ?? 0) + (correct ? 1 : 0);
  next.decisionsWrong = (next.decisionsWrong ?? 0) + (correct ? 0 : 1);

  if (correct) {
    next.stability = clamp((next.stability ?? 0) + 4, 0, 100);
    if (inspection.kind === 'anomaly') {
      next.anomalyLevel = clamp((next.anomalyLevel ?? 0) - 1, 0, 6);
    }
    next = appendLog(next, 'success', t(
      inspection.kind === 'anomaly' ? 'ui.inspectionCorrectAnomaly' : 'ui.inspectionCorrectNormal',
    ));
  } else {
    next.stability = clamp((next.stability ?? 0) - 12, 0, 100);
    next.anomalyLevel = clamp((next.anomalyLevel ?? 0) + 1, 0, 6);
    next = appendLog(next, 'danger', t('ui.inspectionWrong'));
  }

  return { state: checkFailure(next), accepted: true, correct };
}

export function expireInspection(state) {
  if (state.gameOver) return { state, timedOut: false };
  const inspection = state.inspection;
  if (!inspection || inspection.status !== 'pending' || (state.elapsed ?? 0) < inspection.expiresAt) {
    return { state, timedOut: false };
  }

  let next = cloneState(state);
  next.inspection = {
    ...inspection,
    status: 'expired',
    choice: null,
    correct: false,
    resolvedAt: next.elapsed ?? 0,
  };
  next.decisionsWrong = (next.decisionsWrong ?? 0) + 1;
  next.stability = clamp((next.stability ?? 0) - 8, 0, 100);
  next = appendLog(next, 'warn', t('ui.inspectionTimeout'));
  return { state: checkFailure(next), timedOut: true };
}

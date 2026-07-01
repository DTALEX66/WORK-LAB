// archive.js — cross-session anomaly archive (localStorage-backed).
// Survives page reloads and browser restarts on the same device.

const STORAGE_KEY = 'minigame_archive_v1';

const DEFAULT = {
  sessionsPlayed: 0,
  totalAnomaliesTriggered: 0,
  totalLogsUnlocked: 0,
  encounteredAnomalies: {},   // id → count
  unlockedLogs: {},           // id → true
  highestSeverity: 0,
};

/** @returns {typeof DEFAULT} */
export function loadArchive() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return structuredClone(DEFAULT);
    const parsed = JSON.parse(raw);
    return { ...structuredClone(DEFAULT), ...parsed };
  } catch {
    return structuredClone(DEFAULT);
  }
}

export function saveArchive(archive) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(archive));
  } catch {
    // quota exceeded or private browsing — silently skip
  }
}

/**
 * Merge one session's results into the archive.
 * @param {object} sessionSummary
 * @param {number} sessionSummary.anomaliesTriggeredTotal
 * @param {number} sessionSummary.maxAnomalySeverity
 * @param {string[]} sessionSummary.anomalyIds — all anomaly IDs triggered this session
 * @param {string[]} sessionSummary.unlockedLogIds — hidden log IDs unlocked this session
 */
export function commitSessionToArchive(sessionSummary) {
  const archive = loadArchive();
  archive.sessionsPlayed += 1;
  archive.totalAnomaliesTriggered += sessionSummary.anomaliesTriggeredTotal || 0;
  archive.totalLogsUnlocked += sessionSummary.unlockedLogIds?.length || 0;
  archive.highestSeverity = Math.max(archive.highestSeverity, sessionSummary.maxAnomalySeverity || 0);

  for (const id of sessionSummary.anomalyIds || []) {
    archive.encounteredAnomalies[id] = (archive.encounteredAnomalies[id] || 0) + 1;
  }
  for (const id of sessionSummary.unlockedLogIds || []) {
    archive.unlockedLogs[id] = true;
  }
  saveArchive(archive);
  return archive;
}

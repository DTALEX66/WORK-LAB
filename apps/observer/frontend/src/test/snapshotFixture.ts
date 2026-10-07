/** The shared v3 snapshot fixture for the render-level truth tests.
 *
 * One builder, several sweeps. `renderTruthContract.test.tsx` pinned the panel-level rules and
 * `laneTransportTruth.sweep.test.tsx` walks every registry lane with it; if each kept its own copy,
 * a change to "what a healthy snapshot looks like" would silently split the two standards.
 *
 * Everything here is a declared value, never a default: a fixture that quietly filled in `0` or
 * `LIVE` would make a fabricated UI state look correct.
 */
import type { SnapshotV3, Project, TaskRecord, Execution } from '@/types'

/** A fully-populated canonical-store task record (the shape `snapshot_api.py::project_task_record` emits).
 *  Every field is declared, never defaulted: a fixture that padded `0` or `''` would make a fabricated
 *  Inspector value look correct. */
export function mkTaskRecord(over: Partial<TaskRecord> = {}): TaskRecord {
  return {
    taskId: 'WL-900', projectId: 'work-lab', status: 'WAITING_APPROVAL',
    createdAt: '2026-10-08T01:00:00Z', updatedAt: '2026-10-08T01:20:00Z',
    leaseHolder: 'worker-9', leaseExpiresAt: '2026-10-08T01:30:00Z', fencingToken: 7,
    checkpointPresent: true, checkpointKeys: ['cursor', 'stage'],
    checkpointDigest: 'b'.repeat(64),
    ...over,
  }
}

/** An execution row as the v3 projection carries it (no timestamps: the timeline gap is a real gap). */
export function mkExecution(over: Partial<Execution> = {}): Execution {
  return {
    executionId: 'ex-9', anchorProjectId: 'work-lab', workingArea: 'apps/observer',
    state: 'RUNNING', stateQuality: 'strong', agent: 'codex', sessionId: 'sess-42',
    sourceRef: 'git:origin/main@abc1234',
    ...over,
  } as Execution
}

export function mkProject(over: Partial<Project> = {}): Project {
  return {
    projectId: 'work-lab', displayName: 'WORK-LAB', agentPlatform: 'codex',
    identityState: 'RESOLVED', activityState: 'ACTIVE',
    attentionState: 'NONE', activeExecutionCount: 2, workingAreas: ['apps/observer'],
    visibility: 'LOCAL', quality: 'EXACT', lastStrongEvidenceAt: '2026-10-07T08:59:59Z',
    repositories: [],
    git: {
      localSha: 'abc1234def5678', remoteSha: 'abc1234def5678', matchState: 'MATCH',
      branch: 'main', dirtyCount: 3, observedAt: '2026-10-07T09:00:00Z',
      quality: 'EXACT', freshness: 'FRESH', sourceRef: null,
    },
    token: { inputTokens: 64391, outputTokens: 26821, totalTokens: 91212, costQuality: 'ESTIMATED' },
    ci: [], executionIds: ['e1'], sourceRefs: [],
    ...over,
  }
}

export const UNKNOWN_GOVERNANCE: SnapshotV3['governance'] = {
  state: 'UNKNOWN',
  families: {
    rules: { state: 'UNKNOWN', current: null, drift: null },
    skills: { state: 'UNKNOWN', current: null, drift: null },
    memory: { state: 'UNKNOWN', current: null, drift: null },
    adapters: { state: 'UNKNOWN', current: null, drift: null },
  },
}

export function mkSnap(over: Partial<SnapshotV3> = {}): SnapshotV3 {
  return {
    schemaVersion: 'workflow/snapshot/v3',
    revision: 11,
    generatedAt: '2026-10-07T09:12:33Z',
    sourceWatermark: '2026-10-07T09:12:30Z',
    transport: { transportState: 'LIVE', freshnessState: 'FRESH', connectedSince: null, eventsUrl: null },
    coverage: { numerator: 3, denominator: 4, scope: 'collectors' },
    governance: {
      state: 'CLEAN',
      families: {
        rules: { state: 'CLEAN', current: null, drift: 0 },
        skills: { state: 'CLEAN', current: null, drift: 0 },
        memory: { state: 'UNKNOWN', current: null, drift: null },
        adapters: { state: 'CLEAN', current: null, drift: 0 },
      },
    },
    workspace: {},
    projects: [mkProject(), mkProject({ projectId: 'design-lab', displayName: 'DESIGN-LAB', activeExecutionCount: 0 })],
    executions: [],
    tasks: { PENDING: 2 },
    tokenSummary: { inputTokens: 64391, outputTokens: 26821, totalTokens: 91212, costQuality: 'ESTIMATED' },
    git: { localSha: 'abc1234', remoteSha: 'abc1234', ciSha: 'abc1234', matchState: 'MATCH' },
    ci: [],
    sourceRefs: [],
    ...over,
  } as unknown as SnapshotV3
}

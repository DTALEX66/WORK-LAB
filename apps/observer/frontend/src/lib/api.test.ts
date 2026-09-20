// U07 front-truth discipline: the api.ts formatters + projections must keep
// UNKNOWN as UNKNOWN and never fabricate 0 / a monetary amount / a false
// "success". These are the pure functions that carry the whole front's truth
// discipline, so they are the highest-value behavior tests.
import { describe, it, expect } from 'vitest'
import {
  fmtTokens, fmtCostQuality,
  stateTone, activityTone,
  executionsToRows, snapshotToTransportTruth,
} from '@/lib/api'
import type { SnapshotV3, Execution, Project } from '@/types'

function mkSnap(over: Partial<SnapshotV3> = {}): SnapshotV3 {
  return {
    schemaVersion: 'workflow/snapshot/v3',
    revision: 0,
    generatedAt: null,
    sourceWatermark: null,
    transport: {
      transportState: 'UNKNOWN', freshnessState: 'UNKNOWN',
      connectedSince: null, eventsUrl: null,
    },
    coverage: { numerator: null, denominator: null, scope: null },
    governance: {
      state: 'UNKNOWN',
      families: {
        rules: { state: 'UNKNOWN', current: null, drift: null },
        skills: { state: 'UNKNOWN', current: null, drift: null },
        memory: { state: 'UNKNOWN', current: null, drift: null },
        adapters: { state: 'UNKNOWN', current: null, drift: null },
      },
    },
    workspace: {},
    projects: [],
    executions: [],
    tasks: {},
    tokenSummary: { inputTokens: null, outputTokens: null, totalTokens: null, costQuality: 'UNKNOWN' },
    git: { localSha: null, remoteSha: null, ciSha: null, matchState: 'UNKNOWN' },
    ci: [],
    sourceRefs: [],
    ...over,
  }
}

function mkProject(over: Partial<Project> = {}): Project {
  return {
    projectId: 'work-lab', displayName: null, agentPlatform: null,
    identityState: 'UNRESOLVED', activityState: 'REGISTERED',
    attentionState: 'NONE', activeExecutionCount: 0, workingAreas: [],
    visibility: 'UNKNOWN', quality: 'UNKNOWN', lastStrongEvidenceAt: null,
    repositories: [],
    git: { localSha: null, remoteSha: null, matchState: 'UNKNOWN', branch: null, dirtyCount: null, observedAt: null, quality: null, freshness: null, sourceRef: null },
    token: { inputTokens: null, outputTokens: null, totalTokens: null, costQuality: 'UNKNOWN' },
    ci: [], executionIds: [], sourceRefs: [],
    ...over,
  }
}

function mkExec(over: Partial<Execution> = {}): Execution {
  return {
    executionId: 'e1', anchorProjectId: 'work-lab', workingArea: null,
    state: 'UNKNOWN', stateQuality: 'UNKNOWN', agent: null, sessionId: null, sourceRef: null,
    ...over,
  }
}

describe('U07 truth formatters (no fabricated 0 / cost / success)', () => {
  it('fmtTokens: null/undefined -> UNKNOWN, never "0"', () => {
    expect(fmtTokens(null)).toBe('UNKNOWN')
    expect(fmtTokens(undefined)).toBe('UNKNOWN')
    expect(fmtTokens(1234)).toBe('1k')
    expect(fmtTokens(2_500_000)).toBe('2.50M')
  })

  it('fmtCostQuality: absent -> UNKNOWN', () => {
    expect(fmtCostQuality(null)).toBe('UNKNOWN')
    expect(fmtCostQuality(undefined)).toBe('UNKNOWN')
    expect(fmtCostQuality('EXACT')).toBe('EXACT')
  })

  it('stateTone: no silent fallthrough to a positive tone', () => {
    expect(stateTone('RUNNING')).toBe('running')
    expect(stateTone('WAITING_APPROVAL')).toBe('pending')
    expect(stateTone('BLOCKED')).toBe('blocked')
    expect(stateTone('FAILED')).toBe('failed')
    expect(stateTone('COMPLETED')).toBe('done')
    expect(stateTone('UNKNOWN')).toBe('unknown') // not "done"/"running"
  })

  it('activityTone: unknown activity is "unknown", not "active"', () => {
    expect(activityTone('ACTIVE')).toBe('active')
    expect(activityTone('UNKNOWN')).toBe('unknown')
  })
})

describe('U07 projections keep the real v3 shape honest', () => {
  it('executionsToRows: unknown project -> null tokens + UNKNOWN quality (no 0)', () => {
    const snap = mkSnap({
      projects: [], // no matching project
      executions: [mkExec({ anchorProjectId: 'work-lab' })],
    })
    const rows = executionsToRows(snap)
    expect(rows).toHaveLength(1)
    expect(rows[0].totalTokens).toBeNull()
    expect(rows[0].costQuality).toBe('UNKNOWN')
  })

  it('executionsToRows: joins anchor project for real tokens + quality', () => {
    const snap = mkSnap({
      projects: [mkProject({ token: { inputTokens: 10, outputTokens: 5, totalTokens: 15, costQuality: 'EXACT' } })],
      executions: [mkExec()],
    })
    const rows = executionsToRows(snap)
    expect(rows[0].totalTokens).toBe(15)
    expect(rows[0].costQuality).toBe('EXACT')
  })

  it('snapshotToTransportTruth: null snap -> null (no fabricated LIVE)', () => {
    expect(snapshotToTransportTruth(null)).toBeNull()
  })

  it('snapshotToTransportTruth: surfaces real transport state', () => {
    const snap = mkSnap({
      transport: { transportState: 'LIVE', freshnessState: 'FRESH', connectedSince: '2026-01-01T00:00:00Z', eventsUrl: 'http://127.0.0.1:1/api/v1/events' },
      coverage: { numerator: 3, denominator: 4, scope: 'collectors' },
    })
    const t = snapshotToTransportTruth(snap)
    expect(t?.transportState).toBe('LIVE')
    expect(t?.coverageNumerator).toBe(3)
  })
})

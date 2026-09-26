// D3 (2026-09-26 stage D) behavior tests for the primary Work lane.
//
// Pins the prompt's D3 discipline against the REAL v3 snapshot contract:
//   1. the `work` lane is registered and covered exactly once by the 7 groups
//   2. with no snapshot, WorkView shows UNKNOWN/empty markers — never a
//      fabricated "0" execution count, CI count, or task count
//   3. the Inspector shows EXPLICIT source-gap markers for every dimension
//      the v3 snapshot does not carry (Decision refs / Constraints / Next
//      action) — a gap is visible, not a blank cell or fake success
//   4. with a real snapshot, real executions + their anchor project render
//      (the closed loop: project -> execution -> state -> CI -> evidence)
//   5. WorkView is read-only: it renders no approve/dispatch/retry/rollback
//      write affordances (the Observer §8 read-only law)
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { WorkView } from '@/views/WorkView'
import type { SnapshotV3 } from '@/types'
import { VIEW_REGISTRY, VIEW_BY_ID, OVERVIEW_ID } from '@/lib/viewRegistry'
import { NAV_GROUPS } from '@/components/layout/Sidebar'

// Minimal real-shape v3 snapshot (only the fields WorkView reads; the rest
// of the schema is irrelevant to this projection).
function realSnap(): SnapshotV3 {
  const s = {} as unknown as SnapshotV3
  s.schemaVersion = 'workflow/snapshot/v3'
  s.revision = 7
  s.generatedAt = new Date().toISOString()
  s.sourceWatermark = null
  s.transport = {
    transportState: 'LIVE', freshnessState: 'FRESH', connectedSince: null, eventsUrl: null,
  } as SnapshotV3['transport']
  s.coverage = { numerator: 1, denominator: 1, scope: 'workflow' }
  s.governance = {
    state: 'OK',
    families: {
      rules: { state: 'CLEAN', current: null, drift: 0 },
      skills: { state: 'CLEAN', current: null, drift: 0 },
      memory: { state: 'CLEAN', current: null, drift: 0 },
      adapters: { state: 'CLEAN', current: null, drift: 0 },
    },
  }
  s.workspace = {
    plan: { status: 'running', counts: { open: 2, done: 1 } },
    governance: { contracts: 37 },
    history: { totalErrors: 2, recentErrors: [{ errorId: 'ERR-089', title: 'merge gate lesson' }] },
    sources: [{ evidenceKind: 'plan' }],
  }
  s.projects = [{
    projectId: 'work-lab', displayName: 'WORK-LAB', agentPlatform: 'hermes',
    identityState: 'RESOLVED', activityState: 'ACTIVE', attentionState: 'ok',
    activeExecutionCount: 1, workingAreas: ['/repo'], visibility: 'public',
    quality: 'high', lastStrongEvidenceAt: null, repositories: [],
    git: {
      localSha: '279e80e111111111111111111111111111111111', remoteSha: null,
      matchState: 'UNKNOWN', branch: 'main', dirtyCount: 0, observedAt: null,
      quality: null, freshness: null, sourceRef: null,
    },
    token: { inputTokens: 1000, outputTokens: 500, totalTokens: 1500, costQuality: 'UNKNOWN' },
    ci: [{
      runId: '36258547707', workflow: 'wlr-060', headSha: '20f42df111111111111111111111111111111111',
      status: 'success', conclusion: 'success', sourceRef: null,
    }],
    executionIds: ['ex-1'], sourceRefs: ['git:origin/main@279e80e'],
  } as unknown as SnapshotV3['projects'][number]]
  s.executions = [{
    executionId: 'ex-1', anchorProjectId: 'work-lab', workingArea: '/repo',
    state: 'RUNNING', stateQuality: 'strong', agent: 'codex', sessionId: 'sess-9',
    sourceRef: null,
  } as unknown as SnapshotV3['executions'][number]]
  s.tasks = { open: 2, done: 1 }
  s.tokenSummary = { inputTokens: 1000, outputTokens: 500, totalTokens: 1500, costQuality: 'UNKNOWN' }
  s.git = { localSha: '279e80e11111111111111111111111111111111', remoteSha: null, ciSha: '20f42df111111111111111111111111111111111', matchState: 'UNKNOWN' }
  s.ci = [s.projects[0].ci[0]]
  s.sourceRefs = ['git:origin/main@279e80e']
  return s
}

describe('D3 Work lane (read-only closed loop, honest source gaps)', () => {
  it('the work lane is registered and covered exactly once by the 7 nav groups', () => {
    expect(VIEW_BY_ID['work']).toBeDefined()
    expect(VIEW_BY_ID['work'].lane).toBe('work')
    const groupKeys = NAV_GROUPS.map((g) => g.key)
    expect(groupKeys).toHaveLength(7)
    const knownIds = new Set<string>([OVERVIEW_ID, ...VIEW_REGISTRY.map((v) => v.id)])
    const flat = NAV_GROUPS.flatMap((g) => g.ids)
    // `work` is reachable (in some group) and no lane is doubled
    expect(flat.filter((id) => id === 'work')).toHaveLength(1)
    expect(new Set(flat).size).toBe(flat.length)
    expect(new Set(flat)).toEqual(knownIds)
  })

  it('no snapshot -> UNKNOWN markers, never a fabricated 0 count', () => {
    render(<WorkView snap={null} />)
    // '数据源未接入' may appear in several empty-state panes — assert ≥1.
    expect(screen.getAllByText(/数据源未接入/).length).toBeGreaterThanOrEqual(1)
    // the execution pane's empty state must NOT claim "0 条" as if queried
    expect(screen.queryByText('0 条')).toBeNull()
  })

  it('the Inspector surfaces EXPLICIT source gaps for dimensions v3 does not carry', () => {
    render(<WorkView snap={null} />)
    // Decision refs / Constraints / Next action are not in the v3 snapshot ->
    // the gap marker (not a blank, not a fake value) must be visible.
    const gaps = screen.getAllByText(/来源缺口/)
    expect(gaps.length).toBeGreaterThanOrEqual(3)
  })

  it('real snapshot -> the closed loop renders project -> execution -> CI -> evidence', () => {
    const s = realSnap()
    render(<WorkView snap={s} />)
    expect(screen.getByText('ex-1')).toBeTruthy()
    // 'WORK-LAB' renders in both the execution-table anchor cell and the
    // "current projects" pane — assert presence (≥1), not single match.
    expect(screen.getAllByText('WORK-LAB').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/运行中/)).toBeTruthy()
    // CI real conclusion (from the snapshot, not invented)
    expect(screen.getByText('success')).toBeTruthy()
    // Context refs dimension is backed by sourceRefs -> present, not a gap
    expect(screen.getByText(/1 条证据引用/)).toBeTruthy()
  })

  it('WorkView is strictly read-only: zero interactive write affordances', () => {
    // The view is a pure read-only projection: it renders NO <button>/input/
    // textarea at all, so no approve/dispatch/retry/rollback/merge action can
    // be triggered from it (Observer §8 read-only law). Prose that merely
    // mentions those words in a "read-only note" card is allowed; controls
    // are not.
    const { container } = render(<WorkView snap={realSnap()} />)
    expect(container.innerHTML).not.toContain('<button')
    expect(container.innerHTML).not.toContain('<input')
    expect(container.innerHTML).not.toContain('<textarea')
  })
})

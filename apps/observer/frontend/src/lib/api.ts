// WORK-LAB Observer — real data source (sidecar snapshot API)
//
// U06/U07 (taskpack 20260919): the frontend is NO LONGER an authoritative cost
// calculator nor a second Update Authority. The backend canonical projection
// (packages/client-neutral-core/scripts/snapshot_api.py::build_snapshot,
// authoritative in tests/workflow-assistance/test_sidecar_v3_snapshot.py) owns
// every fact. The frontend only projects + formats, and keeps UNKNOWN as
// UNKNOWN. No provider price / FX / quota / Prometheus resource series are
// fabricated here (the v3 snapshot does not carry them).
//
// U06: a typed runtime descriptor replaces the legacy double-appended URL +
// fixed-port single source of truth. The Tauri shell injects a validated
// loopback `?api=` endpoint; the descriptor is the only authoritative path.
import type {
  SnapshotV3, Project, Execution, TokenSummary, CostQuality,
  ExecutionState, ProjectActivityState, TransportState,
} from '@/types'

// backward-compat alias for consumers that imported the old name
export type LiveSnapshot = SnapshotV3

// ---------------------------------------------------------------------------
// U06: typed runtime descriptor. Endpoints are runtime-injected, never
// hardcoded as the source of truth. The browser may read a non-authoritative
// dev-preview default ONLY so a plain `npm` dev server can reach a local
// sidecar; it is labelled `authoritative:false` and never presented as the
// production truth (WLR-140).
// ---------------------------------------------------------------------------
export interface RuntimeDescriptor {
  schemaVersion: 'work-lab/runtime-descriptor/v1'
  snapshotUrl: string
  eventsUrl: string | null
  authoritative: boolean
  source: 'tauri' | 'window-config' | 'static-preview'
}

function _urlParam(name: string): string | null {
  try { return new URLSearchParams(window.location.search).get(name) } catch { return null }
}

// WLR-140 (2026-08-20): endpoints are runtime-injected, never hardcoded.
// Tauri (lib.rs `validated_observer_api`) guarantees `?api=` points at a
// loopback `/api/v1/snapshot` (or `/api/v1/events`) endpoint. If it already IS
// the snapshot endpoint, use it as-is (NO double-append); otherwise treat it as
// a base. The events endpoint is derived, not a second hardcoded port.
export function loadRuntimeDescriptor(): RuntimeDescriptor {
  const api = _urlParam('api')
  if (api) {
    const isSnapshotEndpoint = /\/api\/v1\/snapshot$/.test(api)
    const snapshotUrl = isSnapshotEndpoint ? api : api.replace(/\/$/, '') + '/api/v1/snapshot'
    const eventsUrl = isSnapshotEndpoint
      ? api.replace(/\/api\/v1\/snapshot$/, '/api/v1/events')
      : api.replace(/\/$/, '') + '/api/v1/events'
    return { schemaVersion: 'work-lab/runtime-descriptor/v1', snapshotUrl, eventsUrl, authoritative: true, source: 'tauri' }
  }
  const cfg = (window as unknown as { __OBSERVER_CONFIG__?: { apiBase?: string } }).__OBSERVER_CONFIG__
  if (cfg?.apiBase) {
    const base = String(cfg.apiBase).replace(/\/$/, '')
    return {
      schemaVersion: 'work-lab/runtime-descriptor/v1',
      snapshotUrl: base + '/api/v1/snapshot',
      eventsUrl: base + '/api/v1/events',
      authoritative: true,
      source: 'window-config',
    }
  }
  // NON-AUTHORITATIVE static-preview fallback. This single loopback default lets
  // a dev preview reach a locally-running sidecar; it is explicitly not the
  // production source of truth and must never be shown as authoritative (U06).
  return {
    schemaVersion: 'work-lab/runtime-descriptor/v1',
    snapshotUrl: 'http://127.0.0.1:61867/api/v1/snapshot',
    eventsUrl: 'http://127.0.0.1:61867/api/v1/events',
    authoritative: false,
    source: 'static-preview',
  }
}

const DESCRIPTOR = loadRuntimeDescriptor()
const SNAPSHOT_URL = DESCRIPTOR.snapshotUrl
const EVENTS_URL = DESCRIPTOR.eventsUrl

export async function fetchSnapshot(): Promise<SnapshotV3 | null> {
  try {
    const res = await fetch(SNAPSHOT_URL, { headers: { Origin: SNAPSHOT_URL.replace(/https?:\/\/([^/]+)/, 'http://$1') } })
    if (!res.ok) return null
    return (await res.json()) as SnapshotV3
  } catch {
    return null
  }
}

// ---------------------------------------------------------------------------
// U06: SSE transport. Snapshot -> SSE -> revision/reconnect (Last-Event-ID);
// polling remains only as a fallback. The Tauri shell persists the cursor
// across restarts (lib.rs); the browser keeps it for the session.
// ---------------------------------------------------------------------------
export interface EventStreamHandlers {
  onEvent: (event: MessageEvent, snapshot?: SnapshotV3) => void
  onOpen?: () => void
  onError?: (err: Event) => void
  onReconnect?: (lastEventId: string | null) => void
}

export function openEventStream(handlers: EventStreamHandlers, url: string = EVENTS_URL ?? ''): () => void {
  if (!url) {
    // No authoritative events endpoint available -> only the poll fallback runs.
    handlers.onError?.(new Event('sse-unavailable'))
    return () => { /* nothing to close */ }
  }
  let es: EventSource | null = null
  let lastEventId: string | null = null
  let closed = false
  function connect() {
    if (closed) return
    try { es = new EventSource(url) } catch { handlers.onError?.(new Event('sse-unavailable')); return }
    es.addEventListener('open', () => {
      if (lastEventId) handlers.onReconnect?.(lastEventId)
      handlers.onOpen?.()
    })
    es.addEventListener('snapshot', (ev: MessageEvent) => {
      if (ev.lastEventId) lastEventId = ev.lastEventId
      let snap: SnapshotV3 | undefined
      try { snap = JSON.parse(ev.data) as SnapshotV3 } catch { snap = undefined }
      handlers.onEvent(ev, snap)
    })
    es.addEventListener('message', (ev: MessageEvent) => {
      if (ev.lastEventId) lastEventId = ev.lastEventId
      handlers.onEvent(ev)
    })
    es.addEventListener('error', (err: Event) => {
      // EventSource auto-reconnects on transient errors; report + reset cursor.
      handlers.onError?.(err)
      lastEventId = null
    })
  }
  connect()
  return () => { closed = true; try { es?.close() } catch { /* noop */ } }
}

// ---------------------------------------------------------------------------
// Formatters (backend-truth only; no price / FX / quota computation).
// ---------------------------------------------------------------------------
// WLR-130: unknown stays UNKNOWN, never 0.
export function fmtTokens(n: number | null | undefined): string {
  if (n == null) return 'UNKNOWN'
  return n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : (n / 1e3).toFixed(0) + 'k'
}

// U07: the ONLY cost truth in v3 is a quality label (EXACT/ESTIMATED/UNKNOWN)
// on tokenSummary / project.token. There is no monetary amount in the v3
// snapshot, so the front never fabricates one.
export function fmtCostQuality(q: CostQuality | null | undefined): string {
  return q ?? 'UNKNOWN'
}

// ---------------------------------------------------------------------------
// projections: map the REAL v3 fields into display rows (no phantom fields).
// ---------------------------------------------------------------------------

// One execution row, joined with its anchor project for platform + tokens.
// `cost` is intentionally absent (v3 has no per-execution monetary amount).
export interface AgentRow {
  id: string
  name: string | null
  state: ExecutionState
  agent: string | null
  anchorProjectId: string | null
  workingArea: string | null
  sessionId: string | null
  stateQuality: string
  platform: string | null
  totalTokens: number | null
  costQuality: CostQuality
}

export function executionsToRows(snap: SnapshotV3 | null): AgentRow[] {
  if (!snap) return []
  const byProject = new Map<string, Project>()
  for (const p of snap.projects) byProject.set(p.projectId, p)
  return snap.executions.map((ex: Execution) => {
    const proj = ex.anchorProjectId ? byProject.get(ex.anchorProjectId) : undefined
    return {
      id: ex.executionId || 'exec',
      name: ex.agent || ex.anchorProjectId || 'execution',
      state: ex.state,
      agent: ex.agent,
      anchorProjectId: ex.anchorProjectId,
      workingArea: ex.workingArea,
      sessionId: ex.sessionId,
      stateQuality: ex.stateQuality,
      platform: proj?.agentPlatform ?? null,
      totalTokens: proj?.token.totalTokens ?? null,
      costQuality: proj?.token.costQuality ?? 'UNKNOWN',
    }
  })
}

// Real execution-state -> display tone (no false "success" fallthrough).
export function stateTone(state: ExecutionState): 'running' | 'pending' | 'blocked' | 'failed' | 'done' | 'unknown' {
  switch (state) {
    case 'RUNNING': case 'STARTING': return 'running'
    case 'WAITING_USER': case 'WAITING_APPROVAL': return 'pending'
    case 'BLOCKED': return 'blocked'
    case 'FAILED': return 'failed'
    case 'COMPLETED': return 'done'
    default: return 'unknown'
  }
}

// Project activity -> tone (real v3 activityState set: ACTIVE/REGISTERED/IDLE/UNKNOWN).
export function activityTone(state: ProjectActivityState): 'active' | 'registered' | 'idle' | 'unknown' {
  switch (state) {
    case 'ACTIVE': return 'active'
    case 'REGISTERED': return 'registered'
    case 'IDLE': return 'idle'
    default: return 'unknown'
  }
}

// Real transport truth for the top status bar (never a fake "online").
export interface TransportTruth {
  transportState: TransportState | string
  freshnessState: string
  eventsUrl: string | null
  connectedSince: string | null
  coverageNumerator: number | null
  coverageDenominator: number | null
  coverageScope: string | null
  revision: number | null
}

export function snapshotToTransportTruth(snap: SnapshotV3 | null): TransportTruth | null {
  if (!snap) return null
  const cov = snap.coverage
  return {
    transportState: snap.transport.transportState,
    freshnessState: snap.transport.freshnessState,
    eventsUrl: snap.transport.eventsUrl,
    connectedSince: snap.transport.connectedSince,
    coverageNumerator: cov.numerator,
    coverageDenominator: cov.denominator,
    coverageScope: cov.scope,
    revision: snap.revision,
  }
}

// Token summary (the only token+quality truth).
export function tokenTruth(snap: SnapshotV3 | null): TokenSummary | null {
  return snap?.tokenSummary ?? null
}

// Per-project token rows (for the token/cost panel; costQuality only, no $).
export interface ProjectTokenRow {
  projectId: string
  displayName: string | null
  inputTokens: number | null
  outputTokens: number | null
  totalTokens: number | null
  costQuality: CostQuality
}

export function snapshotToProjectTokens(snap: SnapshotV3 | null): ProjectTokenRow[] {
  if (!snap) return []
  return snap.projects.map((p) => ({
    projectId: p.projectId,
    displayName: p.displayName,
    inputTokens: p.token.inputTokens,
    outputTokens: p.token.outputTokens,
    totalTokens: p.token.totalTokens,
    costQuality: p.token.costQuality,
  }))
}

// ---------------------------------------------------------------------------
// U05 / URL-driven view + theme helpers (used by App.tsx). These read and
// write only the view/theme/layout params so the dashboard is deep-linkable
// and Full/Compact/Dark/Light is real, not a hardcoded class.
// ---------------------------------------------------------------------------
export type ThemeMode = 'dark' | 'light'
export type LayoutMode = 'full' | 'compact'

export function readUrlParam(name: string): string | null {
  try { return new URLSearchParams(window.location.search).get(name) } catch { return null }
}

export function writeUrlParams(view: string, theme: ThemeMode, layout: LayoutMode) {
  if (typeof window === 'undefined') return
  const p = new URLSearchParams()
  if (view) p.set('view', view)
  if (theme !== 'dark') p.set('theme', theme)
  if (layout !== 'full') p.set('layout', layout)
  const qs = p.toString()
  const url = window.location.pathname + (qs ? '?' + qs : '')
  window.history.replaceState(null, '', url)
}


// ---------------------------------------------------------------------------
// useLiveSnapshot: first poll + SSE (U06). Honesty discipline: the initial
// render has NO data -> `live:false`, KPIs render UNKNOWN, and the UI never
// invents agents/models/cost/resources. Data arrives via the first poll, then
// server-sent events keep it fresh; the transport truth is always surfaced.
// ---------------------------------------------------------------------------
import { useEffect, useRef, useState } from 'react'

export interface LiveSnapshotState {
  snap: SnapshotV3 | null
  dataUpdatedAt: number | null
  source: 'live' | 'stale' | 'static-preview'
  live: boolean
  error: string | null
}

export function useLiveSnapshot(pollMs = 5000): LiveSnapshotState {
  const [snap, setSnap] = useState<SnapshotV3 | null>(null)
  const [dataUpdatedAt, setDataUpdatedAt] = useState<number | null>(null)
  const [source, setSource] = useState<LiveSnapshotState['source']>('stale')
  const [live, setLive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    const descriptor = loadRuntimeDescriptor()
    setSource(descriptor.authoritative ? (descriptor.source === 'static-preview' ? 'static-preview' : 'stale') : 'static-preview')
    let closed = false

    const apply = (next: SnapshotV3 | null) => {
      if (closed || !next) return
      setSnap(next)
      setDataUpdatedAt(Date.now())
      setLive(next.transport.transportState === 'LIVE')
      setError(null)
    }

    const tick = async () => {
      try {
        const s = await fetchSnapshot()
        apply(s)
        if (s === null) setError('快照获取失败（数据源离线或端点不可达）— 保持 UNKNOWN，不伪造数据')
      } catch (e) {
        if (!closed) setError(e instanceof Error ? e.message : 'snapshot fetch failed')
      }
    }

    // first poll
    void tick()
    // periodic fallback
    pollRef.current = setInterval(tick, pollMs)

    // SSE primary transport when available
    let closeSse: (() => void) | null = null
    if (descriptor.eventsUrl) {
      try {
        closeSse = openEventStream({
          onEvent: (_ev, s) => apply(s ?? null),
          onOpen: () => setSource(descriptor.authoritative ? 'live' : 'static-preview'),
          onError: () => { /* poll fallback keeps it honest */ },
        })
      } catch { closeSse = null }
    }

    return () => {
      closed = true
      if (pollRef.current) clearInterval(pollRef.current)
      if (closeSse) closeSse()
    }
  }, [pollMs])

  return { snap, dataUpdatedAt, source, live, error }
}

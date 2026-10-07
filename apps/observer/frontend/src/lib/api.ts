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
// The browser must not be steered off that endpoint by a crafted `?api=`: this
// is the client-side mirror of the Rust gate `observer_api_is_loopback_get_only`
// (https, external hosts, credentials in the URL, an added query such as
// `?write=1`, and any non-`/api/v1` path are all refused).
const LOOPBACK_HOST_RE = /^(?:127(?:\.\d{1,3}){3}|localhost|\[::1\])$/i

function _loopbackHttp(raw: string): URL | null {
  try {
    const u = new URL(raw)
    if (u.protocol !== 'http:') return null
    if (!LOOPBACK_HOST_RE.test(u.hostname)) return null
    if (u.username || u.password) return null
    if (u.search || u.hash) return null
    return u
  } catch {
    return null
  }
}

export function isTrustedObserverEndpoint(raw: string): boolean {
  const u = _loopbackHttp(raw)
  return u !== null && /\/api\/v1\/(snapshot|events)$/.test(u.pathname)
}

function _descriptorFromBase(base: string, source: 'tauri' | 'window-config'): RuntimeDescriptor | null {
  const isSnapshot = /\/api\/v1\/snapshot$/.test(base)
  const snapshotUrl = isSnapshot ? base : base.replace(/\/$/, '') + '/api/v1/snapshot'
  const eventsUrl = isSnapshot
    ? base.replace(/\/api\/v1\/snapshot$/, '/api/v1/events')
    : base.replace(/\/$/, '') + '/api/v1/events'
  if (!isTrustedObserverEndpoint(snapshotUrl) || !isTrustedObserverEndpoint(eventsUrl)) return null
  return { schemaVersion: 'work-lab/runtime-descriptor/v1', snapshotUrl, eventsUrl, authoritative: true, source }
}

export function loadRuntimeDescriptor(): RuntimeDescriptor {
  const api = _urlParam('api')
  if (api) {
    // An untrusted injected endpoint is refused outright: it must not even reach
    // the fallback as `authoritative`, and nothing is ever sent to it.
    const d = _descriptorFromBase(api, 'tauri')
    if (d) return d
  }
  const cfg = (window as unknown as { __OBSERVER_CONFIG__?: { apiBase?: string } }).__OBSERVER_CONFIG__
  if (cfg?.apiBase) {
    const d = _descriptorFromBase(String(cfg.apiBase).replace(/\/$/, ''), 'window-config')
    if (d) return d
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

// REQ-RANGE-20261007: `GET /api/v1/evidence-range` is the THIRD endpoint of the same loopback sidecar
// surface. It is derived from the descriptor's snapshot base — never a second hardcoded port — and it has
// to clear the same gate the snapshot endpoint clears (http, literal loopback, no credentials, no added
// query), so a crafted `?api=` cannot steer an evidence read at an external host. The route is GET-only by
// contract; this module exposes no mutating variant.
export function isTrustedEvidenceRangeEndpoint(raw: string): boolean {
  const u = _loopbackHttp(raw)
  return u !== null && u.pathname === '/api/v1/evidence-range'
}

export function evidenceRangeEndpoint(): { url: string; authoritative: boolean } | null {
  const base = _loopbackHttp(SNAPSHOT_URL)
  if (!base) return null
  base.pathname = '/api/v1/evidence-range'
  base.search = ''
  base.hash = ''
  const url = base.toString().replace(/\?$/, '')
  return isTrustedEvidenceRangeEndpoint(url) ? { url, authoritative: DESCRIPTOR.authoritative } : null
}

// Structural read of the wire payload. The front must not cast whatever arrives
// into `SnapshotV3`: a legacy/v2 body, or a truncated one, would then render as
// if it were current truth. Fail closed — `null` is a read failure, so the
// surface keeps the last-good projection and says so.
export function parseSnapshotPayload(value: unknown): SnapshotV3 | null {
  if (!value || typeof value !== 'object') return null
  const s = value as Record<string, unknown>
  if (s.schemaVersion !== 'workflow/snapshot/v3') return null
  if (typeof s.revision !== 'number' || !Number.isFinite(s.revision)) return null
  if (!Array.isArray(s.projects) || !Array.isArray(s.executions)) return null
  for (const k of ['transport', 'coverage', 'tokenSummary', 'governance', 'git']) {
    if (!s[k] || typeof s[k] !== 'object') return null
  }
  return value as SnapshotV3
}

export async function fetchSnapshot(): Promise<SnapshotV3 | null> {
  try {
    const res = await fetch(SNAPSHOT_URL, {
      method: 'GET',
      // A cached snapshot must never be presented as the current one.
      cache: 'no-store',
      headers: { Origin: SNAPSHOT_URL.replace(/https?:\/\/([^/]+)/, 'http://$1') },
    })
    if (!res.ok) return null
    return parseSnapshotPayload(await res.json())
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
  /** a `heartbeat` frame proves the stream is up; it must not cost a snapshot GET */
  onHeartbeat?: (event: MessageEvent) => void
  /** `observed` / `resync_required`: the caller re-reads the canonical snapshot */
  onResync?: () => void
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
      // Same structural gate as the GET: a malformed or legacy frame degrades to
      // "no snapshot" instead of being cast into the typed model.
      try { snap = parseSnapshotPayload(JSON.parse(ev.data)) ?? undefined } catch { snap = undefined }
      handlers.onEvent(ev, snap)
    })
    es.addEventListener('message', (ev: MessageEvent) => {
      if (ev.lastEventId) lastEventId = ev.lastEventId
      handlers.onEvent(ev)
    })
    es.addEventListener('heartbeat', (ev: MessageEvent) => {
      if (ev.lastEventId) lastEventId = ev.lastEventId
      // A heartbeat only proves the stream is up. It must NOT trigger a snapshot
      // GET — that is what keeps a heartbeat burst from becoming a read storm.
      handlers.onHeartbeat?.(ev)
    })
    for (const name of ['observed', 'resync_required']) {
      es.addEventListener(name, (ev: MessageEvent) => {
        if (ev.lastEventId) lastEventId = ev.lastEventId
        handlers.onResync?.()
      })
    }
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

// The snapshot crosses a process boundary (the sidecar may run a different
// build), so a timestamp is localised only when it is strict RFC3339. A value
// the front cannot parse stays UNKNOWN — never the string "Invalid Date".
// The calendar check is not decoration: `Date.parse('2026-02-30T10:00:00Z')`
// does NOT fail, it rolls over to March 2, which would present a corrupt
// timestamp as a plausible one.
const RFC3339_RE = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d+)?(Z|[+-]\d{2}:\d{2})$/
const DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

export function isRfc3339(value: unknown): value is string {
  if (typeof value !== 'string') return false
  const m = RFC3339_RE.exec(value)
  if (!m) return false
  const year = +m[1], month = +m[2], day = +m[3]
  const hour = +m[4], minute = +m[5], second = +m[6]
  if (month < 1 || month > 12) return false
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
  if (day < 1 || day > DAYS_IN_MONTH[month - 1] + (month === 2 && leap ? 1 : 0)) return false
  if (hour > 23 || minute > 59 || second > 60) return false
  if (m[8] !== 'Z') {
    const offHour = +m[8].slice(1, 3), offMinute = +m[8].slice(4, 6)
    if (offHour > 23 || offMinute > 59) return false
  }
  return !Number.isNaN(Date.parse(value))
}

export function fmtTimestamp(
  value: string | null | undefined,
  mode: 'datetime' | 'time' = 'datetime',
): string {
  if (!isRfc3339(value)) return 'UNKNOWN'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return 'UNKNOWN'
  return mode === 'time' ? d.toLocaleTimeString() : d.toLocaleString()
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
  for (const p of snap.projects ?? []) byProject.set(p.projectId, p)
  return (snap.executions ?? []).map((ex: Execution) => {
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
      totalTokens: proj?.token?.totalTokens ?? null,
      costQuality: proj?.token?.costQuality ?? 'UNKNOWN',
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
  const tr = snap.transport
  const cov = snap.coverage
  return {
    transportState: tr?.transportState ?? 'UNKNOWN',
    freshnessState: tr?.freshnessState ?? 'UNKNOWN',
    eventsUrl: tr?.eventsUrl ?? null,
    connectedSince: tr?.connectedSince ?? null,
    coverageNumerator: cov?.numerator ?? null,
    coverageDenominator: cov?.denominator ?? null,
    coverageScope: cov?.scope ?? null,
    revision: snap.revision ?? null,
  }
}

// Token summary (the only token+quality truth).
export function tokenTruth(snap: SnapshotV3 | null): TokenSummary | null {
  return snap?.tokenSummary ?? null
}

// The transport word this surface may claim about ITSELF. A snapshot accepted a
// minute ago carries `transportState: LIVE` forever, so replaying that field
// after the read path fails would advertise a live connection the browser no
// longer has. Absent data is UNKNOWN; a failed read is OFFLINE.
export function frontTransportState(snap: SnapshotV3 | null, live: boolean, error: string | null): string {
  if (!snap) return 'UNKNOWN'
  if (!live && error) return 'OFFLINE'
  return snap.transport?.transportState ?? 'UNKNOWN'
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
  return (snap.projects ?? []).map((p) => ({
    projectId: p.projectId,
    displayName: p.displayName,
    inputTokens: p.token?.inputTokens ?? null,
    outputTokens: p.token?.outputTokens ?? null,
    totalTokens: p.token?.totalTokens ?? null,
    costQuality: p.token?.costQuality ?? 'UNKNOWN',
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

    let lastRevision: number | null = null
    let inFlight = false
    let followUp = false

    const apply = (next: SnapshotV3 | null) => {
      if (closed || !next) return
      // Reject an out-of-order LOWER revision: a delayed older projection must
      // never replace the newer facts already on screen (nor rotate anything).
      if (lastRevision !== null && next.revision < lastRevision) {
        setError('拒绝低于 ' + lastRevision + ' 的乱序投影（revision ' + next.revision + '）— 保持上次良好投影')
        return
      }
      lastRevision = next.revision
      setSnap(next)
      setDataUpdatedAt(Date.now())
      // The payload's own verdict only makes THIS surface live when it came from
      // an authoritative endpoint; a non-authoritative source is never LIVE.
      setLive(descriptor.authoritative && next.transport.transportState === 'LIVE')
      setError(null)
    }

    const reportReadFailure = (message: string) => {
      if (closed) return
      setLive(false)
      setSource(descriptor.authoritative ? 'stale' : 'static-preview')
      setError(message)
    }

    const tick = async () => {
      // Coalesce bursts: one read in flight at a time; a request that arrives
      // while one is running is noted and done once after it — never a stampede,
      // and never a dropped latest read.
      if (inFlight) { followUp = true; return }
      inFlight = true
      try {
        do {
          followUp = false
          const s = await fetchSnapshot()
          if (closed) break
          if (s === null) reportReadFailure('快照获取失败（数据源离线或端点不可达）— 保持 UNKNOWN，不伪造数据')
          else apply(s)
        } while (followUp && !closed)
      } catch (e) {
        reportReadFailure(e instanceof Error ? e.message : 'snapshot fetch failed')
      } finally {
        inFlight = false
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
          onEvent: (_ev, s) => {
            if (s) { apply(s); return }
            // Only a `snapshot` frame that fails the structural gate is a protocol
            // failure; an untyped `message` frame carries no projection and must
            // not degrade the surface.
            if (_ev.type === 'snapshot') {
              reportReadFailure('SSE 帧不合 v3 结构 — 保持上次良好投影，不伪造数据')
            }
          },
          // On (re)connect the stream may be behind us; re-read once to resync.
          onOpen: () => { setSource(descriptor.authoritative ? 'live' : 'static-preview'); void tick() },
          // A stream error stops the LIVE claim immediately (the legacy contract
          // demanded this of the EventSource transport, not of the poll). The next
          // successful read clears it; nothing is wiped and nothing is invented.
          onError: () => reportReadFailure('事件流中断 — 已停止 LIVE 宣称，等待下一次读取恢复'),
          // A heartbeat is proof that the stream is alive: it never costs a
          // snapshot GET and it never manufactures a LIVE data claim.
          onHeartbeat: () => { /* no read, no verdict change */ },
          // observed / resync_required: re-read the canonical snapshot.
          onResync: () => { void tick() },
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

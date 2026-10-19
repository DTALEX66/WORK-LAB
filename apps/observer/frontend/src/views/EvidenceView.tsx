// REQ-RANGE-20261007 · the evidence slice lane: three columns per artifact.
//
// Evidence used to reach this surface as opaque references (an `evidenceKind` string in the Inspector).
// The sidecar now answers exact byte intervals, so a reader can be shown enough to trust one artifact:
//
//   身份 — which artifact this is (handle, the digest the caller recorded for it, its size);
//   切片 — what a range read actually returned (offset, limit, endOffset, eof, the digest of those bytes);
//   判定 — whether the recorded digest agrees, and the backend's typed reason when the read was refused.
//
// What this lane refuses to do:
// * treat HTTP 200 as success. The verdict is `status` / `reason_code` in the body, and the codes are the
//   reader's (`evidence_range_reader.py::REFUSALS`), not labels invented here;
// * show an empty pane where a refusal lives. A REFUSED result carries `content: null`, so the content
//   block is not rendered at all and the reason takes its place;
// * print 0 for a field the result does not carry (an refused read has no offset, no endOffset, no slice
//   digest — `未提供` is the honest cell);
// * offer a hand-typed path field. There is no `<input>` here: an artifact is addressed by a link, the same
//   single `?view=` mechanism the Work lane uses, and the projected shelf is the only source of handles.
//
// WUI-15 (2026-10-20) adds the fourth honest surface of this lane: 证据把手. `artifactHandles` plus
// `artifactHandlesSummary` ride the live v3 payload — a cap-bounded window of identity rows over a much
// larger enumeration — and nothing rendered either key, so a reader could not see which artifacts the
// projection even claims to know about, nor that the window was truncated. The block below states the
// capacity facts, the refusal counters, the snapshot's own ordering rule, and one row per handle. It never
// touches content: the payload says `contentIncluded=false`, and byte reading stays where it lives (the
// range endpoint above). No capacity number is written in this file — every one of them is read from the
// summary, which is what `evidenceHandles.contract.test.tsx` fails on when a literal is typed in here.
import * as React from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { EmptyState, ProductStateCard, UnknownState } from '@/components/ui/states'
import { Dim } from '@/views/RecordInspector'
import { cn } from '@/lib/utils'
import type { ArtifactHandle, ArtifactHandlesSummary, SnapshotV3 } from '@/types'
import type { RecordFocus } from '@/lib/recordFocus'
import { evidenceRangeEndpoint, fmtTimestamp } from '@/lib/api'
import {
  EVIDENCE_RANGE_SCHEMA_VERSION, EVIDENCE_MAX_LIMIT, isRegisteredReasonCode, digestVerdictOf, fmtBytes,
  makeHttpSliceReader, readEvidenceAddress, readEvidenceShelf, evidenceHref,
  type EvidenceAddress, type EvidenceRangeResult, type SliceReader, type EvidenceSliceOutcome,
} from '@/lib/evidenceRange'

type Snap = SnapshotV3 | null

export interface EvidenceViewProps {
  snap: Snap
  focus?: RecordFocus
  onFocus?: (next: RecordFocus) => void
  focusRejected?: string[]
  /** test seam: the slice reader. Production default is the validated loopback GET — never another method. */
  readSlice?: SliceReader
  /** the address to read from; defaults to the live URL search. */
  search?: string
}

const PREVIEW_LIMIT = 1200

/** The three origins the projection can actually distinguish (same vocabulary as RecordInspector/UsageCache). */
type FactOrigin = 'PROJECTED' | 'NULL_FIELD' | 'SOURCE_GAP'

/** A cell that never pads: a value the result does not carry stays 未提供 with the reason it is absent.
 *  `origin` writes the DOM contract marker (`data-origin`) so a reader — and the render-level test — can
 *  tell a projected value from an absent field without reading the prose. */
function Field({ label, value, missing, field, origin }: {
  label: string
  value: string | null
  missing: string
  field?: string
  origin?: FactOrigin
}) {
  return (
    <div
      className="list-item flex-col items-stretch gap-1"
      data-field={field ?? label}
      {...(origin ? { 'data-origin': origin } : {})}
    >
      <div className="text-[12px] uppercase tracking-[0.12em] text-muted">{label}</div>
      {value !== null ? (
        <div className="break-words font-mono text-[12px] text-ink">{value}</div>
      ) : (
        <div className="flex items-center gap-1.5 text-[12px] text-warning">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-secondary" aria-hidden="true" />
          未提供（{missing}）
        </div>
      )}
    </div>
  )
}

const num = (value: number | null | undefined): string | null =>
  typeof value === 'number' && Number.isFinite(value) ? String(value) : null

const bool = (value: boolean | null | undefined, yes: string, no: string): string | null =>
  typeof value === 'boolean' ? (value ? yes : no) : null

const text = (value: string | null | undefined): string | null =>
  value === null || value === undefined || value === '' ? null : value

function statusTone(status: EvidenceRangeResult['status']): 'success' | 'warning' | 'error' {
  return status === 'OK' ? 'success' : status === 'REFUSED' ? 'error' : 'warning'
}

const DIGEST_TONE: Record<string, 'success' | 'warning' | 'error' | 'muted'> = {
  AGREE: 'success', MISMATCH: 'error', UNDETERMINED: 'warning', NOT_REQUESTED: 'muted',
}

const DIGEST_LABEL: Record<string, string> = {
  AGREE: '一致', MISMATCH: '不一致', UNDETERMINED: '未判定', NOT_REQUESTED: '未请求核对',
}

type ReadState =
  | { kind: 'IDLE' }
  | { kind: 'READING' }
  /** `outcome: null` is the no-trusted-endpoint case: a read that could not even be issued. */
  | { kind: 'DONE'; outcome: EvidenceSliceOutcome | null }

export function EvidenceView({
  snap, focus = { taskId: null, executionId: null }, focusRejected = [], readSlice, search,
}: EvidenceViewProps) {
  const initialSearch = search ?? (typeof window === 'undefined' ? '' : window.location.search)
  const verdict = React.useMemo(() => readEvidenceAddress(initialSearch), [initialSearch])
  const [address, setAddress] = React.useState<EvidenceAddress | null>(
    verdict.kind === 'addressed' ? verdict.address : null,
  )
  const [state, setState] = React.useState<ReadState>({ kind: 'IDLE' })

  const endpoint = React.useMemo(() => evidenceRangeEndpoint(), [])
  // The reader lives in a ref on purpose: a caller that passes an inline function must not be able to
  // re-trigger the read on every render (an effect keyed on its identity would loop: read -> state ->
  // new closure -> read). The addressed slice is the only thing that drives a read.
  const readerRef = React.useRef<SliceReader | null>(
    readSlice ?? (endpoint ? makeHttpSliceReader(endpoint.url, endpoint.authoritative) : null),
  )
  readerRef.current = readSlice ?? readerRef.current
  const hasReader = Boolean(readSlice) || endpoint !== null

  // The address is the input; the read follows it. Re-running only happens when the addressed slice changes.
  const addressKey = address ? JSON.stringify(address) : ''
  React.useEffect(() => {
    if (!address) { setState({ kind: 'IDLE' }); return }
    const reader = readerRef.current
    if (!reader) { setState({ kind: 'DONE', outcome: null }); return }
    let cancelled = false
    setState({ kind: 'READING' })
    reader({
      handle: address.handle,
      offset: address.offset, limit: address.limit,
      expectedDigest: address.expectedDigest, wholeDigest: address.wholeDigest,
    }).then((outcome) => { if (!cancelled) setState({ kind: 'DONE', outcome }) })
    return () => { cancelled = true }
  }, [addressKey, hasReader])

  const shelf = readEvidenceShelf(snap)

  const navigate = (next: EvidenceAddress | null) => (event: React.MouseEvent) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey
      || event.shiftKey || event.altKey) return
    event.preventDefault()
    const href = evidenceHref(next, initialSearch)
    window.history.replaceState(null, '', href)
    setAddress(next)
  }

  const rejected = verdict.kind === 'rejected' ? verdict.reasons : []
  const result = state.kind === 'DONE' ? state.outcome : null

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_320px]">
      <div className="flex min-w-0 flex-col gap-4">
        {focusRejected.length > 0 && (
          <Card>
            <CardHeader><span>定位被拒绝</span></CardHeader>
            <CardContent>
              <div className="list">
                {focusRejected.map((reason) => (
                  <div key={reason} className="list-item"><span className="text-warning">{reason}</span></div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {rejected.length > 0 && (
          <Card>
            <CardHeader><span>区间地址被拒绝</span></CardHeader>
            <CardContent>
              <div className="list">
                {rejected.map((reason) => (
                  <div key={reason} className="list-item"><span className="text-warning">{reason}</span></div>
                ))}
              </div>
              <p className="mt-2 text-xs text-muted">
                被拒绝的地址不参与任何读取：这里不会把它拼成一个看起来像句柄的东西，也不会退回清单第一条。
              </p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <span>证据产物 · 投影登记的来源</span>
            <span className="text-[12px] text-muted">
              {shelf.kind === 'sources' ? `${shelf.items.length} 条 · 来自 workspace.sources` : '无投影'}
            </span>
          </CardHeader>
          <CardContent>
            {shelf.kind === 'no-snapshot' ? (
              <div className="empty py-8">
                <div className="icon" aria-hidden="true">◎</div>
                <p className="m-0 text-sm font-semibold text-ink">数据源未接入（保持 UNKNOWN，不预填来源清单）</p>
              </div>
            ) : shelf.kind === 'not-provided' ? (
              <div className="text-xs text-warning">
                来源缺口：v3 快照没有 workspace.sources 字段（生产者未加载仓库证据面），
                因此没有可寻址的句柄。这与「加载了但一个来源都没有」是两件事。
              </div>
            ) : shelf.items.length === 0 ? (
              <div className="text-xs text-muted">已加载证据面，但没有登记任何来源（空列表是查询结果，不是缺源）</div>
            ) : (
              <div className="list">
                {shelf.items.map((item, index) => {
                  const handle = item.path
                  const rowAddress: EvidenceAddress | null = handle
                    ? { handle, offset: null, limit: null, expectedDigest: null, wholeDigest: null }
                    : null
                  const href = evidenceHref(rowAddress, initialSearch)
                  const active = handle !== null && address?.handle === handle
                  return (
                    <div key={`${handle ?? 'row'}-${index}`} className="list-item">
                      <span className="min-w-0 break-words text-[12px] text-ink">
                        {handle
                          ? (
                            <a href={href} onClick={navigate(rowAddress)} className="font-mono" aria-current={active ? 'true' : undefined}>
                              {handle}
                            </a>
                          )
                          : <span className="text-warning">来源缺口：该条目没有 path 字段，无法寻址</span>}
                        {active ? <span className="ml-1.5 text-[12px] text-secondary-ink">已寻址</span> : null}
                      </span>
                      <span className="text-right text-[12px] text-muted">
                        {item.evidenceKind || 'UNKNOWN'} · {item.loadedAt || 'UNKNOWN'}
                        {item.generatedAt ? ` · 生成 ${item.generatedAt}` : ''}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
            <p className="mt-2 text-[12px] text-muted">
              投影登记的 path 是仓库相对路径，而区间读要求绝对句柄，并只在声明的证据面上提供内容。
              点开一条不在证据面上的来源，会得到后端的类型化拒绝，而不是一块空白。
            </p>
            {(focus.taskId || focus.executionId) && (
              <p className="mt-2 text-[12px] text-warning" data-testid="evidence-record-binding">
                记录定位（{[focus.taskId && `taskId=${focus.taskId}`, focus.executionId && `executionId=${focus.executionId}`]
                  .filter(Boolean).join(' · ')}）不会自动变成产物清单：v3 快照没有 record↔artifact 外键，
                绑定它就是把别人的字节挂到这条任务上。证据仍按自己的地址寻址。
              </p>
            )}
          </CardContent>
        </Card>

        <EvidenceHandles snap={snap} search={initialSearch} />

        <Card>
          <CardHeader>
            <span>区间读 · 三列</span>
            <span className="text-[12px] text-muted" data-testid="evidence-endpoint">
              {endpoint
                ? `${endpoint.url} · ${endpoint.authoritative ? '权威注入端点' : '非权威 static-preview 端点'}`
                : '端点不可信（未派生自环回描述符），不发起读取'}
            </span>
          </CardHeader>
          <CardContent>
            <EvidenceColumns address={address} state={state} rejectedCount={rejected.length} result={result} />
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader><span>契约 · worklab/evidence-range-result/v1</span></CardHeader>
          <CardContent>
            <div className="list">
              <Dim label="判定住在 body" value={`status / reason_code；HTTP 200 不等于读取成功（当前 schema ${EVIDENCE_RANGE_SCHEMA_VERSION}）`} />
              <Dim label="拒绝时的内容" value="REFUSED / OUT_OF_RANGE 携带 content=null，本视图不渲染内容块，也不留空白" />
              <Dim label="地址" value="artifact / offset / limit / expectedDigest / wholeDigest 全部走 ?view=evidence 同一条链接机制，没有手填入口" />
              <Dim label="未提供" value="结果里没有的字段显示 未提供，不补 0，也不补 false" />
              <Dim label="上限" value={`单次 ${EVIDENCE_MAX_LIMIT.toLocaleString('en-US')} 字节：超限由后端拒绝（LIMIT_TOO_LARGE），这一侧不做静默截断`} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><span>只读说明</span></CardHeader>
          <CardContent className="text-xs text-muted">
            本视图只发起 <span className="font-mono">GET</span>：没有批准 / 派发 / 重试 / 回滚 / apply 的任何入口，
            也没有写深链。读取失败、被拒绝与未送达是三件不同的事，分别如实呈现；
            项目内部不等于阅读许可 —— 不在声明证据面上的句柄、凭证样名称都由后端拒绝，本视图把拒绝原样展示。
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// WUI-15 · 证据把手（快照声明，不读内容）
//
// The producer publishes two top-level keys next to the evidence shelf: `artifactHandles` (identity rows)
// and `artifactHandlesSummary` (the scope report that says how the rows were chosen). Both were measured on
// a live v3 snapshot and both were invisible here. The rules this block follows, in order:
//
//  * no content, ever, in any direction. `contentIncluded=false` is a statement about the payload, so the
//    block renders no preview, no open-file affordance, no read-bytes link — the range endpoint above is
//    the only thing that can return bytes, and it needs its own address;
//  * no re-ordering. The snapshot owns the order and publishes `orderingRule` saying so; the front end
//    shows the rule and keeps the rows in the sequence it received (a sort here would silently disagree
//    with the disclosure two lines above it);
//  * no padded numbers. A missing count prints 未提供 with its origin, and a count whose runtime shape is
//    not a number — the live `refused.droppedOnVerification` is an object — prints no number at all;
//  * absence is not emptiness. `artifactHandles` undefined is a source gap; `artifactHandles: []` is an
//    enumerated surface with nothing on it. `snap === null` is a third thing again;
//  * the truncation is disclosed, not hidden: 投影 / 枚举 / 省略 / 敏感名拒 / 再生目录剪 ride the header so
//    a reader never mistakes a capped window for the whole repository.
// ---------------------------------------------------------------------------

/** One summary fact: the printed value, and when there is none, why there is none. */
interface Fact { value: string | null; missing: string; origin: FactOrigin }

const absentFact = (label: string): Fact => ({
  value: null,
  missing: `生产者没有给出 ${label} 字段（来源缺口，不预填）`,
  origin: 'SOURCE_GAP',
})

/** A count. Non-numeric runtime shapes keep their shape in the reason and produce no number. */
function countFact(raw: unknown, label: string): Fact {
  if (raw === undefined) return absentFact(label)
  if (raw === null) return { value: null, missing: `${label} 投影为 null —— 未记录，不等于 0`, origin: 'NULL_FIELD' }
  if (typeof raw !== 'number') {
    return {
      value: null,
      missing: `${label} 的形态不是计数（实测 ${Array.isArray(raw) ? 'array' : typeof raw}），不折算成 0`,
      origin: 'NULL_FIELD',
    }
  }
  const value = num(raw)
  return value === null
    ? { value: null, missing: `${label} 不是可表示的数值`, origin: 'NULL_FIELD' }
    : { value, missing: '', origin: 'PROJECTED' }
}

function stringFact(raw: unknown, label: string): Fact {
  if (raw === undefined) return absentFact(label)
  const value = text(typeof raw === 'string' ? raw : null)
  return value === null
    ? { value: null, missing: `${label} 未投影为字符串`, origin: 'NULL_FIELD' }
    : { value, missing: '', origin: 'PROJECTED' }
}

/** A declared boolean, printed with its raw token so the reader can check the wording against the field. */
function flagFact(raw: unknown, label: string, yes: string, no: string): Fact {
  if (raw === undefined) return absentFact(label)
  const value = bool(typeof raw === 'boolean' ? raw : null, yes, no)
  return value === null
    ? { value: null, missing: `${label} 未投影为布尔值`, origin: 'NULL_FIELD' }
    : { value: `${String(raw)} · ${value}`, missing: '', origin: 'PROJECTED' }
}

const seg = (label: string, fact: Fact): string => `${label} ${fact.value ?? 'UNKNOWN'}`

const subRecord = (value: unknown): Record<string, unknown> | null =>
  value !== null && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : null

/** The row's `digest` / `digestSource`. `types.ts::ArtifactHandle` names the seven schema keys only, and
 *  the producer attaches these two to the rows whose digest was recorded — read here rather than
 *  re-declared, so the schema stays the single type authority. */
const rowField = (row: ArtifactHandle, key: 'digest' | 'digestSource'): string | null =>
  text((row as unknown as Record<string, unknown>)[key] as string | null | undefined)

const HANDLES_DIGEST_OPTIONS = [
  { value: 'all', label: '全部' },
  { value: 'recorded', label: '已登记摘要' },
  { value: 'unrecorded', label: '未登记摘要' },
] as const

type HandlesDigestFilter = 'all' | 'recorded' | 'unrecorded'

const HANDLES_PARAM_NAMES = ['handlesSurface', 'handlesDigest'] as const

/** Kept alive while a filter link is followed: the shell's own state, the addressed slice, the filters.
 *  `evidenceHref()` in `lib/evidenceRange.ts` owns the artifact address and its own preserve list; this
 *  lane-local copy exists because a filter must not be able to drop a read that is already addressed. */
const HANDLES_PRESERVED_PARAMS = [
  'theme', 'layout', 'palette', 'api', 'shell', 'taskId', 'executionId',
  'artifact', 'offset', 'limit', 'expectedDigest', 'wholeDigest',
  ...HANDLES_PARAM_NAMES,
] as const

const HANDLES_MAX_SURFACE_LENGTH = 128
const HANDLES_CONTROL_CHARS = /[\u0000-\u001f\u007f]/

interface HandlesFilterVerdict { surface: string | null; digest: HandlesDigestFilter; rejected: string[] }

/** The same discipline as `readEvidenceAddress()`: an illegal value is reported, never applied, and never
 *  answered by falling back to the first option. */
function readHandlesFilters(search: string, knownSurfaces: string[]): HandlesFilterVerdict {
  let params: URLSearchParams
  try { params = new URLSearchParams(search) } catch { return { surface: null, digest: 'all', rejected: [] } }
  const rejected: string[] = []

  const rawSurface = params.get('handlesSurface')
  let surface: string | null = null
  if (rawSurface !== null && rawSurface.trim() !== '') {
    const value = rawSurface.trim()
    if (value.length > HANDLES_MAX_SURFACE_LENGTH) {
      rejected.push(`handlesSurface 超过 ${HANDLES_MAX_SURFACE_LENGTH} 个字符，已拒绝`)
    } else if (HANDLES_CONTROL_CHARS.test(value)) {
      rejected.push('handlesSurface 含控制字符，已拒绝')
    } else if (knownSurfaces.length > 0 && !knownSurfaces.includes(value)) {
      rejected.push(`handlesSurface 不是投影里的证据面（收到 ${value.slice(0, 32)}）：过滤未应用，也不回退成「全部」或第一个面`)
    } else {
      surface = value
    }
  }

  const rawDigest = (params.get('handlesDigest') ?? '').trim()
  let digest: HandlesDigestFilter = 'all'
  if (rawDigest !== '' && rawDigest !== 'all') {
    if (rawDigest === 'recorded' || rawDigest === 'unrecorded') digest = rawDigest
    else rejected.push(`handlesDigest 只接受 all / recorded / unrecorded（收到 ${rawDigest.slice(0, 24)}），已拒绝`)
  }
  return { surface, digest, rejected }
}

/** Filter state travels in the query string — web storage is forbidden in this project — so every filter
 *  click is an address, shareable and stable across a refresh. */
function handlesHref(
  search: string,
  updates: Partial<Record<'handlesSurface' | 'handlesDigest', string | null>>,
): { href: string; search: string } {
  const current = new URLSearchParams(search)
  for (const [name, value] of Object.entries(updates)) {
    if (value === null || value === undefined || value === '') current.delete(name)
    else current.set(name, value)
  }
  const params = new URLSearchParams()
  params.set('view', current.get('view') ?? 'evidence')
  for (const name of HANDLES_PRESERVED_PARAMS) {
    const value = current.get(name)
    if (value !== null && value !== '') params.set(name, value)
  }
  const qs = params.toString()
  const href = `${window.location.pathname}${qs ? `?${qs}` : ''}`
  return { href, search: qs ? `?${qs}` : '' }
}

function handlesChipClass(active: boolean): string {
  return cn(
    'inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[12px] no-underline',
    active ? 'border-primary/70 bg-panel2 text-ink' : 'border-border/60 text-muted hover:text-ink',
  )
}

function EvidenceHandles({ snap, search }: { snap: Snap; search: string }) {
  const rows: ArtifactHandle[] | null = snap && Array.isArray(snap.artifactHandles) ? snap.artifactHandles : null
  const summary: ArtifactHandlesSummary | null = snap?.artifactHandlesSummary ?? null
  // The URL is the state: it is read once at mount (so a refresh with `?handlesDigest=unrecorded` in the
  // address still arrives filtered) and rewritten on every filter click.
  const [filterSearch, setFilterSearch] = React.useState(search)

  const knownSurfaces = React.useMemo(() => {
    const found = new Set<string>()
    for (const row of rows ?? []) {
      if (typeof row.surface === 'string' && row.surface !== '') found.add(row.surface)
    }
    return Array.from(found).sort()
  }, [rows])

  const filters = React.useMemo(
    () => readHandlesFilters(filterSearch, knownSurfaces),
    [filterSearch, knownSurfaces],
  )

  const applyFilter = (
    updates: Partial<Record<'handlesSurface' | 'handlesDigest', string | null>>,
  ) => (event: React.MouseEvent<HTMLAnchorElement>) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey
      || event.shiftKey || event.altKey) return
    event.preventDefault()
    const next = handlesHref(filterSearch, updates)
    window.history.replaceState(null, '', next.href)
    setFilterSearch(next.search)
  }

  const visible = (rows ?? []).filter((row) => {
    if (filters.surface !== null && row.surface !== filters.surface) return false
    if (filters.digest === 'recorded') return row.digestRecorded === true
    if (filters.digest === 'unrecorded') return row.digestRecorded === false
    return true
  })
  // A row without the flag is neither recorded nor unrecorded, so it takes part in no digest filter and
  // says so rather than being counted on the side that happens to be smaller.
  const unflagged = (rows ?? []).filter((row) => typeof row.digestRecorded !== 'boolean').length

  const projectedCount = countFact(summary?.projectedCount, 'projectedCount')
  const enumeratedCount = countFact(summary?.enumeratedCount, 'enumeratedCount')
  const omittedCount = countFact(summary?.omittedCount, 'omittedCount')
  const refusedFacts = subRecord(summary?.refused)
  const sensitiveNames = countFact(refusedFacts?.sensitiveNames, 'refused.sensitiveNames')
  const prunedDirectories = countFact(refusedFacts?.prunedRegenerableDirectories, 'refused.prunedRegenerableDirectories')
  const notRegularFiles = countFact(refusedFacts?.notRegularFiles, 'refused.notRegularFiles')
  const reparseDirectories = countFact(refusedFacts?.reparseDirectories, 'refused.reparseDirectories')
  const unreadableEntries = countFact(refusedFacts?.unreadableEntries, 'refused.unreadableEntries')
  const droppedEntries = Object.values(refusedFacts?.droppedOnVerification ?? {})
    .reduce((total, count) => total + (typeof count === 'number' ? count : 0), 0)
  const droppedCount = countFact(refusedFacts ? droppedEntries : undefined,
                                 'refused.droppedOnVerification')
  // A refusal total is only meaningful when the producer published a refusal record at all; an absent
  // `refused` map stays null so the card cannot appear with invented zeroes.
  const refusalTotal = refusedFacts
    ? [refusedFacts.notRegularFiles, refusedFacts.reparseDirectories, refusedFacts.sensitiveNames,
       refusedFacts.unreadableEntries, refusedFacts.prunedRegenerableDirectories]
        .reduce((total: number, raw) => total + (typeof raw === 'number' ? raw : 0), 0)
      + droppedEntries
    : null
  const capacityLine = [
    seg('投影', projectedCount), seg('枚举', enumeratedCount), seg('省略', omittedCount),
    seg('敏感名拒', sensitiveNames), seg('再生目录剪', prunedDirectories),
  ].join(' / ')

  const digestIndex = subRecord(summary?.digestIndex)
  const cost = subRecord(summary?.cost)
  const content = flagFact(
    summary?.contentIncluded, 'contentIncluded',
    '随快照下发（本区块仍然只列身份，内容渲染归区间读那一侧）',
    '不随快照下发（本区块没有预览 / 打开 / 读取字节的入口）',
  )

  return (
    <Card data-testid="evidence-handles">
      <CardHeader>
        <span>证据把手（快照声明，不读内容）</span>
        <span className="text-[12px] text-muted" data-testid="evidence-handles-count">
          {snap === null ? '把手清单 UNKNOWN · 数据源未接入'
            : rows === null ? '把手清单 UNKNOWN · 快照没有该字段'
            : `可见 ${visible.length} 行 / 投影 ${rows.length} 行`}
        </span>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {snap === null ? (
          <UnknownState
            title="证据把手 UNKNOWN（数据源未接入）"
            description="没有快照就没有把手清单，也没有容量事实：这里不预填行数、不预填枚举量，也不把「读不到」画成「一个把手都没有」。"
            className="py-6"
          />
        ) : (
          <>
            <p className="m-0 text-[12px] text-muted" data-testid="evidence-handles-capacity" data-origin={summary ? 'PROJECTED' : 'SOURCE_GAP'}>
              {capacityLine}
              {summary === null ? ' —— 容量事实未知：快照没有 artifactHandlesSummary 字段，上述每一项都保持 UNKNOWN，不补 0。' : ''}
            </p>

            <div className="flex flex-wrap items-center gap-1.5" data-testid="evidence-handles-truncation">
              <Badge variant="muted">{`顺序 · ${stringFact(summary?.orderingKey, 'orderingKey').value ?? 'UNKNOWN'}`}</Badge>
              <span className="text-[12px] text-muted">
                列表顺序就是快照顺序（生产者按 orderingRule 发布，前端不再排序）。
              </span>
            </div>

            {summary?.truncated === true && (
              <p className="m-0 text-[12px] text-muted" data-testid="evidence-handles-window" data-origin="PROJECTED">
                {`窗口披露：投影 ${projectedCount.value ?? 'UNKNOWN'} 行 / 上限 ${countFact(summary.cap, 'cap').value ?? 'UNKNOWN'}，省略 ${omittedCount.value ?? 'UNKNOWN'} 行 —— 截断是 cap 的设计行为，不是故障；看到的是窗口，不是仓库全量。`}
              </p>
            )}
            {refusalTotal !== null && refusalTotal > 0 && (
              <ProductStateCard
                state="partial-failure"
                subject="证据把手枚举"
                detail={`生产者拒绝或剪枝 ${refusalTotal} 个条目：敏感名 ${sensitiveNames.value ?? '未提供'}、再生目录剪枝 ${prunedDirectories.value ?? '未提供'}、非普通文件 ${notRegularFiles.value ?? '未提供'}、重解析目录 ${reparseDirectories.value ?? '未提供'}、读不动条目 ${unreadableEntries.value ?? '未提供'}、核对时丢弃 ${droppedCount.value ?? '未提供'}。这些位置没有把手行，也没有被折算成"不存在"。`}
                className="py-4 text-left"
              />
            )}


            <div className="flex flex-wrap gap-3" data-testid="evidence-handles-filters">
              <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="按证据面过滤把手">
                <span className="text-[12px] uppercase tracking-[0.12em] text-muted">面 handlesSurface</span>
                <a
                  href={handlesHref(filterSearch, { handlesSurface: null }).href}
                  onClick={applyFilter({ handlesSurface: null })}
                  className={handlesChipClass(filters.surface === null)}
                  aria-current={filters.surface === null ? 'true' : undefined}
                  data-filter-kind="surface"
                  data-filter-value="all"
                >
                  全部面
                </a>
                {knownSurfaces.map((surface) => (
                  <a
                    key={surface}
                    href={handlesHref(filterSearch, { handlesSurface: surface }).href}
                    onClick={applyFilter({ handlesSurface: surface })}
                    className={handlesChipClass(filters.surface === surface)}
                    aria-current={filters.surface === surface ? 'true' : undefined}
                    data-filter-kind="surface"
                    data-filter-value={surface}
                  >
                    {surface}
                  </a>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="按摘要登记状态过滤把手">
                <span className="text-[12px] uppercase tracking-[0.12em] text-muted">摘要 handlesDigest</span>
                {HANDLES_DIGEST_OPTIONS.map((option) => (
                  <a
                    key={option.value}
                    href={handlesHref(filterSearch, { handlesDigest: option.value === 'all' ? null : option.value }).href}
                    onClick={applyFilter({ handlesDigest: option.value === 'all' ? null : option.value })}
                    className={handlesChipClass(filters.digest === option.value)}
                    aria-current={filters.digest === option.value ? 'true' : undefined}
                    data-filter-kind="digest"
                    data-filter-value={option.value}
                  >
                    {option.label}
                  </a>
                ))}
              </div>
            </div>

            {filters.rejected.length > 0 && (
              <div className="list" data-testid="evidence-handles-filter-rejected">
                {filters.rejected.map((reason) => (
                  <div key={reason} className="list-item" data-origin="NULL_FIELD">
                    <span className="text-[12px] text-warning">{reason}</span>
                  </div>
                ))}
              </div>
            )}

            {unflagged > 0 && (
              <p className="m-0 text-[12px] text-warning" data-origin="SOURCE_GAP" data-testid="evidence-handles-unflagged">
                {`其中 ${unflagged} 行没有 digestRecorded 字段：它既不是「已登记」也不是「未登记」，不参与摘要过滤，也不并入任何一侧的计数。`}
              </p>
            )}

            {rows === null ? (
              <div data-testid="evidence-handles-unknown">
                <UnknownState
                  title="证据把手 UNKNOWN（字段缺失）"
                  description="来源缺口：v3 快照没有 artifactHandles 字段（生产者没有发布把手投影）。这与「发布了但一个把手都没有」是两件事，所以这里不画 0 行，也不画空清单。"
                  className="py-6"
                />
              </div>
            ) : rows.length === 0 ? (
              <EmptyState
                title="没有把手行（这是查询结果）"
                description="artifactHandles 是空数组：把手投影跑了，声明的证据面上没有可登记的把手。空列表是答案，不是缺源。"
                className="py-6"
              />
            ) : visible.length === 0 ? (
              <p className="m-0 text-[12px] text-muted" data-testid="evidence-handles-filter-empty" data-origin="PROJECTED">
                {`过滤后没有行：handlesSurface=${filters.surface ?? 'all'} · handlesDigest=${filters.digest} 在投影的 ${rows.length} 行里没有匹配。这是本次过滤的查询结果，投影本身并没有变空。`}
              </p>
            ) : (
              <div className="list" data-testid="evidence-handles-rows" data-ordering="projected">
                {visible.map((row) => (
                  <HandleRow key={row.handle} row={row} />
                ))}
              </div>
            )}

            {summary === null ? (
              <div className="list">
                <div
                  className="list-item flex-col items-stretch gap-1"
                  data-testid="evidence-handles-summary-gap"
                  data-origin="SOURCE_GAP"
                >
                  <div className="text-[12px] uppercase tracking-[0.12em] text-muted">artifactHandlesSummary · 范围报告</div>
                  <div className="flex items-center gap-1.5 text-[12px] text-warning">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-secondary" aria-hidden="true" />
                    来源缺口（当前 v3 快照未携带 artifactHandlesSummary · 生产者没有发布把手的范围报告，
                    cap / 拒绝 / 摘要索引的每一格都保持 UNKNOWN，这里不逐格补 0）
                  </div>
                </div>
              </div>
            ) : (
              <div className="list" data-testid="evidence-handles-summary">
                <Field field="handlesContentIncluded" label="contentIncluded · 内容是否随快照下发" {...factProps(content)} />
                <Field field="handlesEnumerationScope" label="enumerationScope · 枚举范围" {...factProps(stringFact(summary.enumerationScope, 'enumerationScope'))} />
                <Field field="handlesCap" label="cap · 窗口上限" {...factProps(countFact(summary.cap, 'cap'))} />
                <Field field="handlesComplete" label="complete · 枚举是否走完" {...factProps(flagFact(summary.complete, 'complete', '已走完', '未走完'))} />
                <Field field="handlesTruncated" label="truncated · 是否截断" {...factProps(flagFact(summary.truncated, 'truncated', '已截断', '未截断'))} />
                <Field field="handlesGeneratedAt" label="generatedAt · 把手生成时间（整秒精度）" {...factProps(generatedFact(summary.generatedAt))} />
                <Field field="handlesOrderingRule" label="orderingRule · 排序规则（快照原文）" {...factProps(stringFact(summary.orderingRule, 'orderingRule'))} />
                <Field field="handlesRowsWithDigest" label="digestIndex.rowsWithDigest · 有摘要的行" {...factProps(countFact(digestIndex?.rowsWithDigest, 'digestIndex.rowsWithDigest'))} />
                <Field field="handlesRowsWithoutDigest" label="digestIndex.rowsWithoutDigest · 无摘要的行" {...factProps(countFact(digestIndex?.rowsWithoutDigest, 'digestIndex.rowsWithoutDigest'))} />
                <Field field="handlesComputedByHashing" label="digestIndex.computedByHashing · 是否由哈希得到" {...factProps(flagFact(digestIndex?.computedByHashing, 'computedByHashing', '由本侧哈希计算', '取自登记的摘要，界面侧不做哈希'))} />
                <Field field="handlesRecordsScanned" label="digestIndex.recordsScanned · 扫过的登记记录" {...factProps(countFact(digestIndex?.recordsScanned, 'digestIndex.recordsScanned'))} />
                <Field field="handlesRecordsUnreadable" label="digestIndex.recordsUnreadable · 读不动的记录" {...factProps(countFact(digestIndex?.recordsUnreadable, 'digestIndex.recordsUnreadable'))} />
                <Field field="handlesPairsIndexed" label="digestIndex.pairsIndexed · 建索的对数" {...factProps(countFact(digestIndex?.pairsIndexed, 'digestIndex.pairsIndexed'))} />
                <Field field="handlesElapsedMs" label="cost.elapsedMs · 生产者枚举耗时（毫秒）" {...factProps(countFact(cost?.elapsedMs, 'cost.elapsedMs'))} />
                <Field field="handlesEntriesScanned" label="cost.entriesScanned · 扫过的条目" {...factProps(countFact(cost?.entriesScanned, 'cost.entriesScanned'))} />
                <Field field="handlesNotRegularFiles" label="refused.notRegularFiles · 非普通文件" {...factProps(countFact(refusedFacts?.notRegularFiles, 'refused.notRegularFiles'))} />
                <Field field="handlesReparseDirectories" label="refused.reparseDirectories · 重解析目录" {...factProps(countFact(refusedFacts?.reparseDirectories, 'refused.reparseDirectories'))} />
                <Field field="handlesUnreadableEntries" label="refused.unreadableEntries · 读不动的条目" {...factProps(countFact(refusedFacts?.unreadableEntries, 'refused.unreadableEntries'))} />
                <Field field="handlesDroppedOnVerification" label="refused.droppedOnVerification · 核对时丢弃" {...factProps(countFact(refusedFacts?.droppedOnVerification, 'refused.droppedOnVerification'))} />
                <Field field="handlesSchemaVersion" label="schemaVersion · 摘要契约版本" {...factProps(stringFact(summary.schemaVersion, 'schemaVersion'))} />
              </div>
            )}

            <p className="m-0 text-[12px] text-muted" data-testid="evidence-handles-boundary">
              每一行只有身份元数据：handle / kind / surface / surfaceRoot / sizeBytes / modifiedAt / digestRecorded；
              digest 与 digestSource 只出现在登记过摘要的那部分行上，其数量由上面的
              digestIndex.rowsWithDigest / rowsWithoutDigest 披露，本视图不自己数行。
              时间戳是整秒精度，同一秒内的先后按快照自己的 orderingRule 决定（原文见上），本视图不补毫秒、不补时区，
              也不把缺失的摘要显示成空串。快照声明 contentIncluded=false，
              所以这里没有任何预览、打开文件或读取字节的入口：字节只能由区间读端点按地址返回。
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}

/** `generatedAt` is an RFC3339 string; a value that fails the shape check stays UNKNOWN via fmtTimestamp. */
function generatedFact(raw: unknown): Fact {
  const base = stringFact(raw, 'generatedAt')
  if (base.value === null || base.origin !== 'PROJECTED') return base
  return fmtTimestamp(base.value) === 'UNKNOWN'
    ? { value: null, missing: 'generatedAt 不是可解析的 RFC3339 时间', origin: 'NULL_FIELD' }
    : { value: `${fmtTimestamp(base.value)} · 源值 ${base.value} · 整秒`, missing: '', origin: 'PROJECTED' }
}

function factProps(fact: Fact): { value: string | null; missing: string; origin: FactOrigin } {
  return { value: fact.value, missing: fact.missing, origin: fact.origin }
}

/** One projected handle. No link: the row is a declaration of identity, and turning it into a byte read
 *  would be exactly the affordance `contentIncluded=false` forbids this block from offering. */
function HandleRow({ row }: { row: ArtifactHandle }) {
  // `null` and "no key" stay different facts: a projected null is a NULL_FIELD, an absent key is a source gap.
  const size = countFact(row.sizeBytes, 'sizeBytes')
  const modified = stringFact(row.modifiedAt, 'modifiedAt')

  const timeCell = (() => {
    if (modified.value === null) {
      return { text: `时间未提供（${modified.missing}）`, origin: modified.origin, precision: undefined as 'second' | undefined }
    }
    const formatted = fmtTimestamp(modified.value)
    if (formatted === 'UNKNOWN') {
      return {
        text: `时间未提供（modifiedAt 不是可解析的 RFC3339 时间：源值 ${modified.value}）`,
        origin: 'NULL_FIELD' as FactOrigin,
        precision: undefined as 'second' | undefined,
      }
    }
    return {
      text: `${formatted} · 整秒精度 · 源值 ${modified.value}`,
      origin: 'PROJECTED' as FactOrigin,
      precision: 'second' as const,
    }
  })()

  const digestCell = (() => {
    const recorded = rowField(row, 'digest')
    if (row.digestRecorded === true) {
      if (recorded !== null) {
        const source = rowField(row, 'digestSource')
        return {
          text: `摘要已登记 · ${recorded}${source ? ` · 来源 ${source}` : ' · 摘要来源未投影'}`,
          origin: 'PROJECTED' as FactOrigin,
        }
      }
      return {
        text: '摘要登记为已记录，但投影里没有摘要值 · 不显示空串冒充摘要',
        origin: 'NULL_FIELD' as FactOrigin,
      }
    }
    if (row.digestRecorded === false) {
      return { text: '摘要未记录 · 该把手没有登记摘要（不是空摘要，也不是零）', origin: 'NULL_FIELD' as FactOrigin }
    }
    return {
      text: '摘要状态未投影 · 该行没有 digestRecorded 字段，既不按已记录也不按未记录处理',
      origin: 'SOURCE_GAP' as FactOrigin,
    }
  })()

  return (
    <div
      className="list-item flex-col items-stretch gap-1"
      data-handle-row={row.handle}
      data-handles-surface={text(row.surface) ?? ''}
      data-digest-recorded={typeof row.digestRecorded === 'boolean' ? String(row.digestRecorded) : 'absent'}
    >
      <div className="flex min-w-0 flex-wrap items-baseline justify-between gap-2">
        <span className="min-w-0 break-all font-mono text-[12px] text-ink">{text(row.handle) ?? '未提供（handle 字段缺失）'}</span>
        <span className="text-[12px] text-muted tabular-nums" data-handles-cell="size" data-origin={size.origin}>
          {size.value !== null ? `${fmtBytes(row.sizeBytes)} · 源值 ${size.value} B` : `大小未提供（${size.missing}）`}
        </span>
      </div>
      <div className="flex min-w-0 flex-wrap gap-2 text-[12px] text-muted">
        <span data-handles-cell="surface" data-origin={text(row.surface) === null ? 'NULL_FIELD' : 'PROJECTED'}>
          面 {text(row.surface) ?? '未提供'}
        </span>
        <span className="break-all" data-handles-cell="surfaceRoot" data-origin={text(row.surfaceRoot) === null ? 'NULL_FIELD' : 'PROJECTED'}>
          根 {text(row.surfaceRoot) ?? '未提供（该生产者不发 surfaceRoot）'}
        </span>
        <span data-handles-cell="kind" data-origin={text(row.kind) === null ? 'NULL_FIELD' : 'PROJECTED'}>
          类 {text(row.kind) ?? '未提供'}
        </span>
        <span
          data-handles-cell="modifiedAt"
          data-origin={timeCell.origin}
          {...(timeCell.precision ? { 'data-precision': timeCell.precision } : {})}
        >
          {timeCell.text}
        </span>
        <span data-handles-cell="digest" data-origin={digestCell.origin}>{digestCell.text}</span>
      </div>
    </div>
  )
}

function EvidenceColumns({
  address, state, rejectedCount, result,
}: {
  address: EvidenceAddress | null
  state: ReadState
  rejectedCount: number
  result: EvidenceSliceOutcome | null
}) {
  const nothingAddressed = address === null

  if (nothingAddressed) {
    return (
      <div className="three-col" data-testid="evidence-columns" data-state={rejectedCount > 0 ? 'rejected' : 'unaddressed'}>
        <Card data-column="identity">
          <CardHeader><span>身份 · Identity</span></CardHeader>
          <CardContent>
            <Field label="handle" value={null} missing={rejectedCount > 0 ? '地址被拒绝，没有可用句柄' : '地址里没有 artifact 参数，未指定句柄'} />
            <Field label="记录摘要" value={null} missing="未指定句柄，谈不上摘要" />
            <Field label="大小" value={null} missing="未发起读取" />
          </CardContent>
        </Card>
        <Card data-column="slice">
          <CardHeader><span>切片 · Slice</span></CardHeader>
          <CardContent>
            <Field label="offset" value={null} missing="未发起读取" />
            <Field label="limit" value={null} missing="未发起读取" />
            <Field label="endOffset" value={null} missing="未发起读取" />
            <Field label="eofReached" value={null} missing="未发起读取" />
            <Field label="sliceDigest" value={null} missing="未发起读取" />
          </CardContent>
        </Card>
        <Card data-column="verdict">
          <CardHeader><span>判定 · Verdict</span></CardHeader>
          <CardContent>
            <div className="text-xs text-muted" role="status">
              {rejectedCount > 0
                ? '无判定：地址在校验处就被拒绝，读取未发起。被拒绝的值不会被拼成一个看起来像句柄的东西，也不会退回清单第一条。'
                : '无判定：没有句柄就没有对象。选择左侧清单里的一条来源，或直接使用带 artifact 参数的地址。'}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (state.kind === 'IDLE' || state.kind === 'READING') {
    return (
      <div className="three-col" data-testid="evidence-columns" data-state="reading" role="status">
        <Card data-column="identity">
          <CardHeader><span>身份 · Identity</span></CardHeader>
          <CardContent><Field label="handle" value={address?.handle ?? null} missing="地址被拒绝" /></CardContent>
        </Card>
        <Card data-column="slice">
          <CardHeader><span>切片 · Slice</span></CardHeader>
          <CardContent>
            <div className="text-xs text-muted">
              正在按精确区间读取（{state.kind === 'READING' ? '请求已发出，尚无判定' : '请求未发出：无可用端点'}）。
              在判定到达之前不显示任何计数，避免把「还没读」画成「读到 0」。
            </div>
          </CardContent>
        </Card>
        <Card data-column="verdict">
          <CardHeader><span>判定 · Verdict</span></CardHeader>
          <CardContent>
            <Badge variant="muted">{state.kind === 'READING' ? '读取中' : '无端点'}</Badge>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="three-col" data-testid="evidence-columns" data-state="no-endpoint">
        <Card data-column="identity">
          <CardHeader><span>身份 · Identity</span></CardHeader>
          <CardContent><Field label="handle" value={address?.handle ?? null} missing='地址里没有 artifact' /></CardContent>
        </Card>
        <Card data-column="slice">
          <CardHeader><span>切片 · Slice</span></CardHeader>
          <CardContent><Field label="offset" value={null} missing="读取未发起" /></CardContent>
        </Card>
        <Card data-column="verdict">
          <CardHeader><span>判定 · Verdict</span></CardHeader>
          <CardContent>
            <div className="text-xs text-warning">来源缺口：没有可信的环回端点，未发起读取（这不是拒绝，也不是空结果）</div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (result.kind !== 'RESULT') {
    // A read that never arrived is not a refusal: no reason_code may be written for it.
    const detail = result.kind === 'UNREACHABLE' ? result.detail : result.why
    return (
      <div className="three-col" data-testid="evidence-columns" data-state="unreachable">
        <Card data-column="identity">
          <CardHeader><span>身份 · Identity</span></CardHeader>
          <CardContent>
            <Field label="handle" value={address?.handle ?? null} missing="地址未被解析" />
            <Field label="记录摘要" value={address?.expectedDigest ?? null} missing="地址未提供 expectedDigest" />
            <Field label="大小" value={null} missing="未送达，没有实测大小" />
          </CardContent>
        </Card>
        <Card data-column="slice">
          <CardHeader><span>切片 · Slice</span></CardHeader>
          <CardContent>
            <Field label="offset" value={num(address?.offset ?? undefined)} missing="地址未提供 offset（后端使用其默认）" />
            <Field label="limit" value={num(address?.limit ?? undefined)} missing="地址未提供 limit（后端使用其默认）" />
            <Field label="endOffset" value={null} missing="没有返回字节" />
            <Field label="sliceDigest" value={null} missing="没有返回字节" />
          </CardContent>
        </Card>
        <Card data-column="verdict">
          <CardHeader><span>判定 · Verdict</span></CardHeader>
          <CardContent>
            <div className="list-item flex-col items-stretch gap-1">
              <div className="text-[12px] uppercase tracking-[0.12em] text-muted">状态</div>
              <div className="text-[12px] text-warning">
                无判定（读取未送达） · {detail}
                {result.kind === 'UNREACHABLE' && result.httpStatus !== null ? ` · HTTP ${result.httpStatus}` : ''}
              </div>
            </div>
            <div className="text-[12px] text-muted">
              后端没有给出判定码，所以这里不写拒绝码、不写判定结果，也不写字节计数。
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const item = result.result
  const identity = item.identity
  const cost = item.cost
  const digest = digestVerdictOf(item)
  const sizeBytes = typeof identity?.sizeBytes === 'number' ? identity.sizeBytes : (typeof cost?.fileSize === 'number' ? cost.fileSize : null)
  const recordedDigest = text(address?.expectedDigest) ?? text(identity?.wholeDigest)
  const isOk = item.status === 'OK'

  return (
    <div className="three-col" data-testid="evidence-columns" data-state={item.status} data-reason={item.reason_code}>
      <Card data-column="identity">
        <CardHeader><span>身份 · Identity</span></CardHeader>
        <CardContent>
          <Field field="handle" label="handle" value={text(item.handle) ?? text(address?.handle)} missing="结果未回传句柄" />
          <Field field="recordedDigest" label="记录摘要（调用方提供）" value={recordedDigest} missing="地址未提供 expectedDigest，后端也没有可比的 wholeDigest" />
          <Field field="digestSource" label="摘要来源" value={text(identity?.digestSource)} missing="该判定未走到摘要核对" />
          <Field field="size" label="大小" value={sizeBytes !== null ? fmtBytes(sizeBytes) : null} missing="结果未携带文件大小" />
        </CardContent>
      </Card>

      <Card data-column="slice">
        <CardHeader><span>切片 · Slice</span></CardHeader>
        <CardContent>
          <Field field="offset" label="offset" value={num(item.offset)} missing={`${item.reason_code} 未走到区间定位`} />
          <Field field="limit" label="limit" value={num(item.limit) ?? num(address?.limit ?? undefined)} missing="地址与结果都没有 limit，后端使用其默认上限" />
          <Field field="bytesRequested" label="bytesRequested" value={num(item.bytesRequested)} missing={`${item.reason_code} 没有请求字节数`} />
          <Field field="endOffset" label="endOffset" value={num(item.endOffset)} missing={`${item.reason_code} 没有返回区间`} />
          <Field field="eofReached" label="eofReached" value={bool(item.eofReached, '是（已到文件尾）', '否（仍有后续字节）')} missing={`${item.reason_code} 没有返回区间`} />
          <Field field="sliceDigest" label="sliceDigest" value={text(item.sliceDigest)} missing="没有返回字节，因此没有切片摘要" />
          <Field field="bytesRead" label="本次读取" value={isOk && typeof cost?.bytesRead === 'number' ? `${fmtBytes(cost.bytesRead)} / ${fmtBytes(sizeBytes)}` : null} missing={`${item.status} 不是读取成功：拒绝信封里的 bytesRead 是占位值，不是一次读取的成本`} />
          <Field field="wholeRead" label="是否整读" value={isOk && typeof cost?.wholeFileWasRead === 'boolean' ? (cost.wholeFileWasRead ? '是（整份文件被读完）' : '否（只读了这一段）') : null} missing={`${item.status} 没有走到读取，因此没有整读与否的实测`} />
        </CardContent>
      </Card>

      <Card data-column="verdict">
        <CardHeader><span>判定 · Verdict</span></CardHeader>
        <CardContent>
          <div className="list-item flex-col items-stretch gap-1">
            <div className="text-[12px] uppercase tracking-[0.12em] text-muted">状态 / 判定码</div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={statusTone(item.status)}>{`${item.status} · ${item.reason_code}`}</Badge>
              {!isRegisteredReasonCode(item.reason_code) && (
                <span className="text-[12px] text-warning">未登记的判定码（后端新增，UI 未镜像）</span>
              )}
            </div>
            <div className="break-words text-[12px] text-ink">{item.reason || '后端未给出原因文本'}</div>
            <div className="text-[12px] text-muted">
              传输层 HTTP {result.httpStatus} —— 判定取自响应体，不取自状态码
            </div>
          </div>

          <div className="list-item flex-col items-stretch gap-1" data-testid="evidence-digest-verdict">
            <div className="text-[12px] uppercase tracking-[0.12em] text-muted">摘要一致性</div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={DIGEST_TONE[digest.kind]}>{`${DIGEST_LABEL[digest.kind]} · ${digest.kind}`}</Badge>
            </div>
            <div className="break-words text-[12px] text-ink">{digest.detail}</div>
          </div>

          {isOk && typeof item.content === 'string' ? (
            <div className="list-item flex-col items-stretch gap-1" data-testid="evidence-content">
              <div className="text-[12px] uppercase tracking-[0.12em] text-muted">
                返回字节预览 · [{num(item.offset)}, {num(item.endOffset)})
              </div>
              <pre className="m-0 max-h-40 overflow-auto whitespace-pre-wrap break-words font-mono text-[12px] text-ink">
                {item.content.length > PREVIEW_LIMIT ? `${item.content.slice(0, PREVIEW_LIMIT)}…（预览截断，完整区间由 sliceDigest 署名）` : item.content}
              </pre>
            </div>
          ) : (
            <div className="list-item flex-col items-stretch gap-1" data-testid="evidence-no-content">
              <div className="text-[12px] uppercase tracking-[0.12em] text-muted">内容</div>
              <div className="text-[12px] text-warning">
                没有返回字节（{item.status === 'REFUSED' ? '后端拒绝携带内容' : '空区间'}），因此这里没有内容块可看。
                拒绝是判定，不是空面板。
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

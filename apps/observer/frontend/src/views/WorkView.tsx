// D3 (Lite visible delivery, 9/26 stage D) · L10b (2026-09-27): the "Work" lane —
// the first user-visible read-only closed loop:
//   real entry -> current project -> real task/execution detail ->
//   state & failure reason -> Context / Evidence -> locate next step.
//
// Left pane = what the REAL v3 snapshot contract can back right now
// (executions / task buckets / CI runs / plan status). Right pane = the
// Inspector (Authority / Constraints / Context refs / Decision refs /
// Source refs / Evidence / Known failures / Next action).
//
// L10b: the B10 surfaces (`.panel` cards, `.table` execution table,
// `.list` / `.list-item` rows, `.tag` state pills) replace the ad-hoc utility
// styling, and the old amber source-gap marker now uses the brand-locked
// warning/cyan language (no warm-gold accent).
//
// Discipline (prompt D3 + B5, unchanged): the Observer is strictly read-only
// and projects ONLY fields the backend v3 snapshot actually carries. Any
// Inspector dimension the current contract does NOT carry is rendered as an
// EXPLICIT "source gap" (来源缺口) marker — never a fabricated 0, empty
// success, or a new parallel ledger. This is not a second CURRENT.
import * as React from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { SnapshotV3, Execution, Project, CiRun, TaskRecord } from '@/types'
import { fmtTokens, fmtCostQuality, stateTone } from '@/lib/api'
// P1-02: record focus is one query parameter per record, resolved against the records the backend
// actually carries. The lane mechanism (?view=) is unchanged and no second router exists.
import { EMPTY_FOCUS, recordLink, resolveFocus, type RecordFocus } from '@/lib/recordFocus'

type Snap = SnapshotV3 | null

export interface WorkViewProps {
  snap: Snap
  focus?: RecordFocus
  onFocus?: (next: RecordFocus) => void
  /** ids the URL carried that the validator refused, with the reason for each. */
  focusRejected?: string[]
}

const STATE_TEXT: Record<string, string> = {
  RUNNING: '运行中', STARTING: '启动中', WAITING_USER: '待用户', WAITING_APPROVAL: '待审批',
  BLOCKED: '受阻', COMPLETED: '完成', FAILED: '失败', UNKNOWN: '未知',
}

function toneVariant(tone: string): 'success' | 'warning' | 'error' | 'info' | 'muted' {
  switch (tone) {
    case 'running': return 'success'
    case 'pending': case 'blocked': return 'warning'
    case 'failed': return 'error'
    case 'done': return 'info'
    default: return 'muted'
  }
}

// A single Inspector dimension. When `value` is empty we show an explicit
// source-gap marker, NOT a blank cell or a fake "0" — the prompt requires the
// gap to be visible so the user knows what is / is not wired yet.
function Dim({ label, value, hint }: { label: string; value: React.ReactNode; hint?: string }) {
  const present = value !== null && value !== undefined && value !== '' && value !== false
  return (
    <div className="list-item flex-col items-stretch gap-1">
      <div className="text-[10px] uppercase tracking-[0.12em] text-muted">{label}</div>
      {present ? (
        <div className="whitespace-pre-wrap text-[11px] text-ink">{value}</div>
      ) : (
        <div className="flex items-center gap-1.5 text-[11px] text-warning">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-secondary" aria-hidden="true" />
          来源缺口（当前 v3 快照未携带{hint ? ` · ${hint}` : ''}）
        </div>
      )}
    </div>
  )
}

export function WorkView({
  snap, focus = EMPTY_FOCUS, onFocus = () => {}, focusRejected = [],
}: WorkViewProps) {
  const exs: Execution[] = snap?.executions || []
  const projects: Project[] = snap?.projects || []
  const ci: CiRun[] = snap?.ci || []
  const tasks = snap?.tasks
  const taskRows = tasks ? Object.entries(tasks) : []
  const plan = (snap?.workspace as any)?.plan

  const byProject = new Map<string, Project>()
  for (const p of projects) byProject.set(p.projectId, p)

  // Inspector data sources — each reads ONLY a real v3 field; absent -> gap.
  const sourceRefs: string[] = snap?.sourceRefs || []
  const contractCount = (snap?.workspace as any)?.governance?.contracts
  const knownFailures = (snap?.workspace as any)?.history?.recentErrors || []
  const evidenceSources: any[] = (snap?.workspace as any)?.sources || []

  // P1-02 — the focused record, resolved against the records this projection actually carries.
  // `taskRecords === undefined` (the producer never queried) and `[]` (queried, none) are kept apart.
  const taskRecords: TaskRecord[] | undefined = snap?.taskRecords
  const taskState = resolveFocus(focus.taskId, taskRecords, (record) => record.taskId)
  const executionState = resolveFocus(
    focus.executionId,
    snap ? snap.executions : undefined,
    (record: Execution) => record.executionId,
  )
  const selectedTask = taskState.kind === 'matched' ? taskState.record : null
  const selectedExecution = executionState.kind === 'matched' ? executionState.record : null

  const selectTask = (taskId: string | null) => onFocus({ taskId, executionId: focus.executionId })
  const selectExecution = (executionId: string | null) => onFocus({ taskId: focus.taskId, executionId })
  const clearFocus = () => onFocus(EMPTY_FOCUS)

  // Read-only law (Observer §8): this lane renders no <button>/input/textarea, so a record cannot be
  // "acted on" from here. A record is therefore addressed with the one primitive that is not an action:
  // a real link. Its href IS the deep link — right-click copy, middle-click open and a pasted URL all
  // resolve to the same record, and the SPA click handler only prevents the reload.
  const laneHref = (next: RecordFocus) => recordLink(
    'work',
    next,
    typeof window === 'undefined' ? '' : window.location.search,
  )
  const linkClick = (next: RecordFocus, apply: () => void) => (event: React.MouseEvent) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
    event.preventDefault()
    apply()
  }
  const origin = typeof window === 'undefined' ? '' : window.location.origin
  const shareUrl = laneHref({ taskId: focus.taskId, executionId: focus.executionId })

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_320px]">
      {/* -------- Left pane: the real Work contract the snapshot backs -------- */}
      <div className="flex min-w-0 flex-col gap-4">
        {focusRejected.length > 0 && (
          <Card>
            <CardHeader><span>定位被拒绝</span></CardHeader>
            <CardContent className="flex flex-col gap-2">
              <div className="list">
                {focusRejected.map((reason) => (
                  <div key={reason} className="list-item">
                    <span className="text-warning">{reason}</span>
                    <a href={laneHref(EMPTY_FOCUS)} onClick={linkClick(EMPTY_FOCUS, clearFocus)} className="text-xs text-muted">清除定位</a>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted">非法标识不参与任何查询；记录请从下方列表选择。</p>
            </CardContent>
          </Card>
        )}

        {(taskState.kind === 'not-found' || taskState.kind === 'backend-not-provided') && (
          <Card>
            <CardHeader><span>任务定位</span></CardHeader>
            <CardContent className="flex items-start justify-between gap-3">
              {taskState.kind === 'not-found' ? (
                <div className="flex flex-col gap-1">
                  <Badge variant="error">记录不存在</Badge>
                  <p className="text-xs text-muted">
                    快照里没有 taskId=<span className="font-mono">{taskState.wanted}</span> 的任务：
                    可能已删除、属于其他项目，或后端还没把它投影进 v3 快照。
                    这里不自动改选第一条记录 —— 展示另一条任务比展示空白更糟。
                  </p>
                </div>
              ) : (
                <div className="flex flex-col gap-1">
                  <Badge variant="warning">后端未提供</Badge>
                  <p className="text-xs text-muted">
                    当前快照没有 taskRecords 字段（生产者未查询任务表），无法定位
                    taskId=<span className="font-mono">{focus.taskId}</span>。
                    这与「查询过但没有任务」是两件事，所以不写成「无任务」。
                  </p>
                </div>
              )}
              <a href={laneHref(EMPTY_FOCUS)} onClick={linkClick(EMPTY_FOCUS, clearFocus)} className="shrink-0 text-xs">清除定位</a>
            </CardContent>
          </Card>
        )}

        {selectedTask && (
          <Card>
            <CardHeader>
              <span>任务详情 · <span className="font-mono">{selectedTask.taskId || 'UNKNOWN'}</span></span>
              <span className="flex items-center gap-2 text-[11px] text-muted">
                {/* No clipboard button lives here: a read-only lane gets no control. The address below
                    is selectable text, and every link in this lane already points at exactly it. */}
                <a href={laneHref(EMPTY_FOCUS)} onClick={linkClick(EMPTY_FOCUS, clearFocus)}>取消定位</a>
              </span>
            </CardHeader>
            <CardContent>
              <div className="list">
                <Dim label="Task ID" value={selectedTask.taskId || null}
                  hint="任务标识来自 canonical store 的 tasks 表" />
                <Dim label="Project" value={selectedTask.projectId || null} hint="任务归属项目" />
                <Dim label="Status" value={selectedTask.status || null}
                  hint="真实状态；状态机里没有的写法原样显示，不改写成成功" />
                <Dim label="Lease / Fencing"
                  value={selectedTask.leaseHolder
                    ? `${selectedTask.leaseHolder} · fence ${selectedTask.fencingToken ?? 'UNKNOWN'} · 到期 ${selectedTask.leaseExpiresAt || 'UNKNOWN'}`
                    : null}
                  hint="当前无持有者时为 null，不是 0" />
                <Dim label="Checkpoint 身份"
                  value={selectedTask.checkpointPresent
                    ? `键 ${selectedTask.checkpointKeys.join(' / ') || '（无键）'} · digest ${selectedTask.checkpointDigest ? selectedTask.checkpointDigest.slice(0, 12) : 'UNKNOWN'}`
                    : null}
                  hint="检查点正文不进入只读投影，只投影键名与摘要（摘要随正文变化）" />
                <Dim label="创建 / 更新"
                  value={selectedTask.updatedAt ? `${selectedTask.createdAt || 'UNKNOWN'} → ${selectedTask.updatedAt}` : null} />
                <Dim label="Goal" value={null}
                  hint="目标文本属提示词面，只读投影不带正文" />
                <Dim label="Revision / Attempt" value={null}
                  hint="修订与尝试由 Task Ledger 合同持有，尚未进入快照投影" />
                <Dim label="Planner / Agent Routes" value={null} hint="计划与路由未投影" />
                <Dim label="Execution Timeline" value={null}
                  hint="v3 快照没有 task↔execution 外键，因此不假装列出「该任务的执行」" />
                <Dim label="Diff / Tests / exact-SHA CI" value={null}
                  hint="CI 运行是项目级的，未与任务绑定；不冒充任务级验证" />
                <Dim label="Receipts / Approval / Handoff" value={null} hint="回执、审批与交接未投影" />
                <Dim label="Next Action" value={null} hint="下一步由操作员判定；Observer 只读" />
              </div>
              <p className="mt-2 break-all font-mono text-[10px] text-muted" data-testid="work-focus-link">{origin}{shareUrl}</p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <span>执行详情</span>
            <span className="text-[11px] text-muted">
              {exs.length} 条 · 真实投影{snap ? '' : ' · 数据源未接入'}
            </span>
          </CardHeader>
          <CardContent>
            {exs.length === 0 ? (
              <div className="empty py-10">
                <div className="icon" aria-hidden="true">◎</div>
                <p className="m-0 text-sm font-semibold text-ink">
                  暂无执行记录{snap ? '（registry 中无 active execution）' : '（数据源未接入，保持 UNKNOWN）'}
                </p>
              </div>
            ) : (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>执行 / 目标</th>
                      <th>项目</th>
                      <th>状态</th>
                      <th>会话</th>
                      <th>工作区</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exs.map((e) => {
                      const proj = e.anchorProjectId ? byProject.get(e.anchorProjectId) : undefined
                      return (
                        <tr key={e.executionId}>
                          <td className="font-mono text-muted">
                            {/* The row link IS the deep link (?view=work&executionId=...). Selecting a
                                record is navigation, not an action, so the lane keeps its zero-control
                                read-only law. */}
                            <a
                              href={laneHref({ taskId: focus.taskId, executionId: e.executionId })}
                              onClick={linkClick({ taskId: focus.taskId, executionId: e.executionId }, () => selectExecution(e.executionId))}
                              className="font-mono"
                              aria-current={e.executionId === focus.executionId ? 'true' : undefined}
                            >
                              {e.executionId}
                            </a>
                            {e.executionId === focus.executionId ? (
                              <span className="ml-1.5 text-[10px] text-secondary">已定位</span>
                            ) : null}
                          </td>
                          <td className="text-ink">{proj?.displayName || e.anchorProjectId || 'UNKNOWN'}</td>
                          <td>
                            <Badge variant={toneVariant(stateTone(e.state))}>{STATE_TEXT[e.state] || e.state}</Badge>
                            {e.stateQuality ? <span className="ml-1.5 text-[10px] text-muted">{e.stateQuality}</span> : null}
                          </td>
                          <td className="font-mono text-[10px] text-muted">{e.sessionId || 'UNKNOWN'}</td>
                          <td className="font-mono text-[10px] text-muted">{e.workingArea || 'UNKNOWN'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <span>任务记录</span>
            <span className="text-[11px] text-muted">
              {taskRecords === undefined
                ? '后端未提供（快照无 taskRecords 字段）'
                : `${taskRecords.length} 条 · 真实投影${snap ? '' : ' · 数据源未接入'}`}
            </span>
          </CardHeader>
          <CardContent>
            {taskRecords === undefined ? (
              <div className="text-xs text-warning">
                来源缺口：v3 快照没有 taskRecords 字段。没有记录可读，任务级定位就没有可指向的对象，
                这里不画一张没有源的卡片。
              </div>
            ) : taskRecords.length === 0 ? (
              <div className="empty py-8">
                <div className="icon" aria-hidden="true">◎</div>
                <p className="m-0 text-sm font-semibold text-ink">
                  无任务记录（已查询 canonical store 的 tasks 表，结果为空）
                </p>
              </div>
            ) : (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>任务</th>
                      <th>项目</th>
                      <th>状态</th>
                      <th>更新</th>
                      <th>Checkpoint</th>
                    </tr>
                  </thead>
                  <tbody>
                    {taskRecords.map((record, index) => {
                      const id = record.taskId || `row-${index}`
                      return (
                        <tr key={id}>
                          <td className="font-mono text-muted">
                            <a
                              href={laneHref({ taskId: record.taskId, executionId: focus.executionId })}
                              onClick={linkClick({ taskId: record.taskId, executionId: focus.executionId }, () => selectTask(record.taskId))}
                              className="font-mono"
                              aria-current={record.taskId && record.taskId === focus.taskId ? 'true' : undefined}
                            >
                              {record.taskId || 'UNKNOWN'}
                            </a>
                            {record.taskId && record.taskId === focus.taskId ? (
                              <span className="ml-1.5 text-[10px] text-secondary">已定位</span>
                            ) : null}
                          </td>
                          <td className="text-ink">{record.projectId || 'UNKNOWN'}</td>
                          <td>
                            <Badge variant={record.status && ['RUNNING', 'QUEUED'].includes(record.status) ? 'success' : 'muted'}>
                              {record.status || 'UNKNOWN'}
                            </Badge>
                          </td>
                          <td className="font-mono text-[10px] text-muted">{record.updatedAt || 'UNKNOWN'}</td>
                          <td className="font-mono text-[10px] text-muted">
                            {record.checkpointPresent ? `digest ${record.checkpointDigest ? record.checkpointDigest.slice(0, 8) : 'UNKNOWN'}` : 'null'}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="two-col">
          <Card>
            <CardHeader><span>任务状态桶 + 计划</span></CardHeader>
            <CardContent>
              {plan?.status ? (
                <div className="mb-2 flex items-center gap-2 text-xs">
                  <span className="text-muted">计划</span>
                  <Badge variant={plan.status === 'done' ? 'info' : 'warning'}>{plan.status}</Badge>
                  {plan.counts ? <span className="text-[10px] text-muted">
                    {Object.entries(plan.counts).map(([k, v]) => `${k}=${v}`).join(' · ')}
                  </span> : null}
                </div>
              ) : null}
              {taskRows.length === 0 ? (
                <div className="text-xs text-muted">任务桶：{snap ? '0（registry 无桶）' : 'UNKNOWN（数据源未接入）'}</div>
              ) : (
                <div className="list">
                  {taskRows.map(([k, v]) => (
                    <div key={k} className="list-item">
                      <span className="text-muted">{k}</span>
                      <span className="tabular-nums text-ink">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><span>CI 运行（真实结论）</span></CardHeader>
            <CardContent>
              {ci.length === 0 ? (
                <div className="text-xs text-muted">无 CI 记录{snap ? '' : '（数据源未接入）'}</div>
              ) : (
                <div className="list">
                  {ci.slice(0, 5).map((r, i) => (
                    <div key={i} className="list-item">
                      <span className="min-w-0 truncate font-mono text-muted">{r.headSha ? r.headSha.slice(0, 7) : 'UNKNOWN'} · {r.workflow || 'UNKNOWN'}</span>
                      <Badge variant={r.conclusion === 'success' ? 'success' : r.conclusion === 'failure' ? 'error' : 'muted'}>
                        {r.conclusion || r.status || 'UNKNOWN'}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {projects.length > 0 && (
          <Card>
            <CardHeader><span>当前项目</span></CardHeader>
            <CardContent>
              <div className="list">
                {projects.slice(0, 6).map((p) => (
                  <div key={p.projectId} className="list-item">
                    <span className="text-ink">{p.displayName || p.projectId}</span>
                    <span className="ml-3 text-right text-muted">
                      {p.agentPlatform || 'UNKNOWN'} · 活动 {p.activityState} · Token {fmtTokens(p.token.totalTokens)} ({fmtCostQuality(p.token.costQuality)})
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* -------- Right pane: Inspector (explicit source gaps, read-only) -------- */}
      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader><span>Inspector · 证据与引用</span></CardHeader>
          <CardContent>
            <div className="list">
              <Dim label="Authority"
                value={contractCount != null ? `治理合同 ${String(contractCount)} 份` : null}
                hint="合同计数由 workspace.governance 携带" />
              <Dim label="Context refs"
                value={sourceRefs.length ? `${sourceRefs.length} 条证据引用` : null}
                hint="来源引用由 snapshot.sourceRefs 携带" />
              <Dim label="Source refs"
                value={sourceRefs.length ? sourceRefs.slice(0, 4).join('\n') : null} />
              <Dim label="Evidence"
                value={evidenceSources.length ? `${evidenceSources.length} 个来源（${evidenceSources.map((s: any) => s.evidenceKind || 'unknown').join(' / ')}）` : null}
                hint="来源由 workspace.sources 携带" />
              <Dim label="Decision refs"
                value={null}
                hint="决策引用未进入 v3 快照 —— 需授权接入，暂不为可见闭环伪造" />
              <Dim label="Constraints"
                value={null}
                hint="约束面未进入 v3 快照 —— 暂不为可见闭环伪造" />
              <Dim label="Known failures"
                value={knownFailures.length ? knownFailures.slice(0, 5).map((e: any) => `${e.errorId || 'ERR-?'} ${e.title || ''}`.trim()).join(' · ') : null}
                hint="失败由 workspace.history.recentErrors 携带" />
              <Dim label="Next action"
                value={null}
                hint="下一步由操作员判定；Observer 只读，不自动派生 / 不伪造" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><span>只读说明</span></CardHeader>
          <CardContent className="text-xs text-muted">
            本视图严格只读：仅投影 Workflow 所有方公开的 v3 快照字段；未携带的维度以
            <span className="text-warning"> 来源缺口</span> 显式呈现，不伪造 0 / 成功，
            也不新建第二份账本。写操作（批准 / 派发 / 合并 …）只进入获准的 Control
            Surface，不属于 Observer。
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

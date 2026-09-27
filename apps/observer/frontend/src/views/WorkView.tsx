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
import type { SnapshotV3, Execution, Project, CiRun } from '@/types'
import { fmtTokens, fmtCostQuality, stateTone } from '@/lib/api'

type Snap = SnapshotV3 | null

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

export function WorkView({ snap }: { snap: Snap }) {
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

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_320px]">
      {/* -------- Left pane: the real Work contract the snapshot backs -------- */}
      <div className="flex min-w-0 flex-col gap-4">
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
                          <td className="font-mono text-muted">{e.executionId}</td>
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

// UI_VIEWS (20260921): Audit Trail lane — read-only projection of CI runs,
// executions and source refs. HONEST: empty => EmptyState, no write actions,
// no fabricated rows. Filtering/sorting are local view state only.
import * as React from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/ui/states'
import { Select } from '@/components/ui/input'
import type { CiRun, Execution } from '@/types'

interface AuditRow {
  key: string
  kind: 'CI' | '执行'
  ref: string
  status: string
  conclusion: string
  sourceRef: string | null
}

function ciVariant(status: string, conclusion: string | null): 'success' | 'error' | 'warning' | 'muted' {
  const c = (conclusion ?? status).toLowerCase()
  if (c === 'success' || c === 'succeeded' || c === 'completed') return 'success'
  if (c === 'failure' || c === 'failed' || c === 'timed_out' || c === 'cancelled' || c === 'canceled') return 'error'
  if (c === 'pending' || c === 'in_progress' || c === 'running' || c === 'queued') return 'warning'
  return 'muted'
}

function execVariant(state: string): 'success' | 'error' | 'warning' | 'muted' {
  switch (state) {
    case 'COMPLETED': return 'success'
    case 'FAILED': return 'error'
    case 'RUNNING':
    case 'STARTING':
    case 'WAITING_USER':
    case 'WAITING_APPROVAL': return 'warning'
    default: return 'muted'
  }
}

export function AuditTrailView({ snap }: { snap: any }) {
  const ci: CiRun[] = Array.isArray(snap?.ci) ? snap.ci : []
  const executions: Execution[] = Array.isArray(snap?.executions) ? snap.executions : []
  const sourceRefs: string[] = Array.isArray(snap?.sourceRefs) ? snap.sourceRefs : []

  const [filter, setFilter] = React.useState<'all' | 'ci' | 'exec' | 'failed'>('all')

  const rows: AuditRow[] = React.useMemo(() => {
    const out: AuditRow[] = [
      ...ci.map((r, i) => ({
        key: `ci-${i}`,
        kind: 'CI' as const,
        ref: `${r.workflow ?? 'CI'} @ ${(r.headSha || 'UNKNOWN').slice(0, 8)}${r.runId ? ` · run ${r.runId}` : ''}`,
        status: r.status ?? 'UNKNOWN',
        conclusion: r.conclusion ?? 'UNKNOWN',
        sourceRef: r.sourceRef,
      })),
      ...executions.map((e) => ({
        key: `ex-${e.executionId}`,
        kind: '执行' as const,
        ref: `${e.executionId}${e.agent ? ` · ${e.agent}` : ''}`,
        status: e.state,
        conclusion: e.stateQuality,
        sourceRef: e.sourceRef,
      })),
    ]
    // stable sort: CI first (by runId, then ref), then executions (by id)
    out.sort((a, b) =>
      a.kind === b.kind ? a.ref.localeCompare(b.ref) : a.kind === 'CI' ? -1 : 1,
    )
    return out
  }, [ci, executions])

  const visible = rows.filter((r) => {
    if (filter === 'ci') return r.kind === 'CI'
    if (filter === 'exec') return r.kind === '执行'
    if (filter === 'failed') {
      const c = r.conclusion.toLowerCase()
      return c === 'failure' || c === 'failed' || c === 'timed_out'
    }
    return true
  })

  return (
    <div className="flex flex-col gap-4 overflow-auto p-4">
      <Card>
        <CardHeader>
          <span>审计追踪（只读）</span>
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-muted">{visible.length} 条记录</span>
            <Select
              value={filter}
              onChange={(e) => setFilter((e.target.value as typeof filter))}
              aria-label="按类型筛选"
              className="h-8 w-32 text-[11px]"
            >
              <option value="all">全部</option>
              <option value="ci">CI 运行</option>
              <option value="exec">执行</option>
              <option value="failed">失败</option>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {visible.length === 0 ? (
            ci.length === 0 && executions.length === 0 ? (
              <EmptyState
                title="无审计记录"
                description="当前快照未携带 CI 运行或执行记录。Observer 保持 UNKNOWN，不伪造历史。"
              />
            ) : (
              <div className="py-6 text-center text-xs text-muted">该筛选条件下无记录</div>
            )
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[11px]">
                <thead>
                  <tr className="border-b border-border text-muted">
                    <th className="py-2 pr-3 font-medium">类型</th>
                    <th className="py-2 pr-3 font-medium">引用</th>
                    <th className="py-2 pr-3 font-medium">状态</th>
                    <th className="py-2 pr-3 font-medium">结论</th>
                    <th className="py-2 font-medium">来源引用</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((r) => (
                    <tr key={r.key} className="border-b border-border/40 last:border-0">
                      <td className="py-2 pr-3 text-muted">{r.kind}</td>
                      <td className="py-2 pr-3 font-mono">{r.ref}</td>
                      <td className="py-2 pr-3">
                        <Badge variant={r.kind === 'CI' ? ciVariant(r.status, r.conclusion) : execVariant(r.status)}>
                          {r.status}
                        </Badge>
                      </td>
                      <td className="py-2 pr-3">{r.conclusion}</td>
                      <td className="py-2 font-mono text-muted break-all">
                        {r.sourceRef ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><span>来源引用（{sourceRefs.length}）</span></CardHeader>
        <CardContent>
          {sourceRefs.length === 0 ? (
            <div className="py-4 text-center text-xs text-muted">无来源引用</div>
          ) : (
            <ul className="flex flex-col gap-1 font-mono text-[11px] text-muted">
              {sourceRefs.map((s, i) => (
                <li key={i} className="truncate">{s}</li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><span>原则</span></CardHeader>
        <CardContent className="text-xs text-muted">
          审计追踪为纯只读视图：可筛选、可排序，但不提供任何重试 / 撤销 / 重放操作按钮。
          数据全部来自后端投影（ci[] / executions[] / sourceRefs），缺失即 UNKNOWN。
        </CardContent>
      </Card>
    </div>
  )
}

// L10 (2026-09-27): B10 Overview / 总览 — the landing surface.
// B10 structure 1:1: 4-col KPI grid (glow big numbers) + two-col trend +
// split recent-executions + Observer map (read-only radial graph) + system
// status metric boxes + alerts. All values are the REAL v3 snapshot
// projection; B5 discipline preserved: without a snapshot the three fact
// KPIs read UNKNOWN (never a fabricated 0) and the "数据源未接入" honest
// indicator is present.
import * as React from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { KPICard } from '@/components/dashboard/KPICard'
import { ExecutionTable } from '@/components/dashboard/ExecutionTable'
import { ProjectPanel } from '@/components/dashboard/ProjectPanel'
import { TokenPanel } from '@/components/dashboard/TokenPanel'
import { NodeGraph, type GraphNode } from '@/components/graph/node-graph'
import { Sparkline } from '@/components/ui/sparkline'
import { StatusPill } from '@/components/ui/status'
import { ListView, type ListItem } from '@/components/ui/list'
import { Badge } from '@/components/ui/badge'
import {
  fmtCostQuality, tokenTruth, executionsToRows,
  type LiveSnapshotState,
} from '@/lib/api'
import type { SnapshotV3 } from '@/types'

export interface OverviewViewProps {
  snap: SnapshotV3 | null
  source: LiveSnapshotState['source']
  live: boolean
}

function fmtTokensSafe(tt: ReturnType<typeof tokenTruth>): string {
  if (!tt || tt.totalTokens == null) return 'UNKNOWN'
  const n = tt.totalTokens
  return n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : (n / 1e3).toFixed(0) + 'k'
}

export function OverviewView({ snap, source, live }: OverviewViewProps) {
  const tt = tokenTruth(snap)
  const rows = executionsToRows(snap)
  const activeExecs = rows.filter((r) => r.state === 'RUNNING' || r.state === 'STARTING').length
  const tr = snap?.transport
  const cov = snap?.coverage

  // Alerts = honest signals only: failed CI runs / failed executions /
  // transport OFFLINE. No fabricated alert counts.
  const alerts: ListItem[] = React.useMemo(() => {
    const out: ListItem[] = []
    for (const r of snap?.ci || []) {
      if (r.conclusion === 'failure' || r.conclusion === 'cancelled') {
        out.push({ leading: r.runId ?? '—', title: `${r.workflow ?? 'CI'} 失败`, sub: r.headSha ? `@ ${r.headSha.slice(0, 8)}` : undefined, state: { text: r.conclusion ?? 'failure', variant: 'error' } })
      }
    }
    for (const r of rows) {
      if (r.state === 'FAILED' || r.state === 'BLOCKED') {
        out.push({ leading: r.id, title: '执行受阻 / 失败', sub: r.name || r.id, state: { text: r.state, variant: 'error' } })
      }
    }
    if (tr && tr.transportState === 'OFFLINE') {
      out.push({ title: '数据源离线', sub: 'sidecar 快照不可达', state: { text: 'OFFLINE', variant: 'error' } })
    }
    return out.slice(0, 8)
  }, [snap, rows, tr])

  // Observer map nodes: the 6 projection entities; "active" only when a real
  // running execution references that entity dimension.
  const runningAgents = new Set(rows.filter((r) => r.state === 'RUNNING' || r.state === 'STARTING').map((r) => r.platform).filter((p): p is string => !!p))
  const graphNodes: GraphNode[] = [
    { id: 'agent', label: 'Agent', state: runningAgents.size ? 'active' : 'idle' },
    { id: 'workflow', label: 'Workflow', state: 'idle' },
    { id: 'tool', label: 'Tool', state: 'idle' },
    { id: 'mcp', label: 'MCP', state: 'idle' },
    { id: 'memory', label: 'Memory', state: 'idle' },
    { id: 'taskpack', label: 'Task Pack', state: 'idle' },
  ]

  return (
    <div className="flex flex-col gap-4">
      {/* B10 `.kpi-grid` — 4 columns; first three are FACT KPIs (B5: UNKNOWN
          without a snapshot, never 0) */}
      <div className="grid grid-cols-4 gap-4">
        <KPICard title="项目" value={snap ? String(snap.projects.length) : 'UNKNOWN'} sub={snap ? 'registry' : '数据源未接入'} />
        <KPICard title="活跃执行" value={snap ? String(activeExecs) : 'UNKNOWN'} sub={'共 ' + (snap ? String(rows.length) : '—') + ' 条'} />
        <KPICard title="Token" value={snap ? fmtTokensSafe(tt) : 'UNKNOWN'} sub={'质量 ' + fmtCostQuality(tt?.costQuality)} />
        <KPICard title="数据源" value={live ? 'LIVE' : snap ? source.toUpperCase() : 'UNKNOWN'} sub={snap ? 'revision ' + String(snap.revision) : '等待数据'} />
      </div>

      {/* B10 `.two-col` — execution trend + token trend (honest empty when no series) */}
      <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1.2fr))' }}>
        <Card className="wl-card-hover">
          <CardHeader>
            <span>执行趋势</span>
            <Badge variant="muted">{rows.length} 条记录</Badge>
          </CardHeader>
          <CardContent>
            <Sparkline values={[]} height={150} />
          </CardContent>
        </Card>
        <Card className="wl-card-hover">
          <CardHeader>
            <span>Token 用量趋势</span>
            <Badge variant="muted">{fmtCostQuality(tt?.costQuality)}</Badge>
          </CardHeader>
          <CardContent>
            <Sparkline values={[]} height={150} />
          </CardContent>
        </Card>
      </div>

      {/* B10 `.split` — recent executions + observer map & system status */}
      <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1.35fr))' }}>
        <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
          <div className="panel2 rounded-md p-4 min-h-[300px]">
            <ExecutionTable rows={snap ? rows : []} hasData={!!snap} />
          </div>
          <div className="flex flex-col gap-4">
            <ProjectPanel snap={snap} />
            <TokenPanel snap={snap} />
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <Card className="wl-card-hover">
            <CardHeader>
              <span>Observer Map（只读拓扑）</span>
              <StatusPill variant={live ? 'success' : 'muted'}>{live ? 'LIVE' : snap ? 'STALE' : 'OFFLINE'}</StatusPill>
            </CardHeader>
            <CardContent>
              <NodeGraph core="Observer" nodes={graphNodes} className="min-h-[300px]" />
            </CardContent>
          </Card>

          <Card className="wl-card-hover">
            <CardHeader><span>系统状态（真实传输）</span></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                <div className="panel2 rounded-lg border border-border/62 p-3.5">
                  <div className="text-[11px] text-muted">传输</div>
                  <div className="mt-1 text-lg font-bold text-ink tabular-nums">{tr?.transportState || 'UNKNOWN'}</div>
                </div>
                <div className="panel2 rounded-lg border border-border/62 p-3.5">
                  <div className="text-[11px] text-muted">新鲜度</div>
                  <div className="mt-1 text-lg font-bold text-ink tabular-nums">{tr?.freshnessState || 'UNKNOWN'}</div>
                </div>
                <div className="panel2 rounded-lg border border-border/62 p-3.5">
                  <div className="text-[11px] text-muted">覆盖</div>
                  <div className="mt-1 text-lg font-bold text-ink tabular-nums">
                    {cov && cov.numerator != null ? `${cov.numerator}/${cov.denominator ?? '?'}` : 'UNKNOWN'}
                  </div>
                </div>
                <div className="panel2 rounded-lg border border-border/62 p-3.5">
                  <div className="text-[11px] text-muted">修订</div>
                  <div className="mt-1 text-lg font-bold text-ink tabular-nums">{snap ? String(snap.revision) : 'UNKNOWN'}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="wl-card-hover">
            <CardHeader>
              <span>告警（真实信号）</span>
              <span className="text-[11px] text-muted">{alerts.length ? `${alerts.length} 条` : '无'}</span>
            </CardHeader>
            <CardContent>
              {alerts.length ? (
                <ListView items={alerts} />
              ) : (
                <div className="py-5 text-center text-xs text-muted">
                  {snap ? '当前无告警信号（无失败 CI / 无受阻执行 / 传输在线）' : '数据源未接入 — 无法判断告警（保持 UNKNOWN，不伪造"全部正常"）'}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="wl-card-hover">
            <CardHeader><span>最近任务包</span></CardHeader>
            <CardContent>
              {snap?.tasks && Object.keys(snap.tasks).length ? (
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(snap.tasks).slice(0, 6).map(([family, count]) => (
                    <div key={family} className="panel2 rounded-lg border border-border/62 p-3">
                      <div className="text-[11px] text-muted">{family}</div>
                      <div className="text-xl font-bold text-secondary tabular-nums">{count}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-5 text-center text-xs text-muted">数据源未接入 — 无任务包计数（UNKNOWN）</div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

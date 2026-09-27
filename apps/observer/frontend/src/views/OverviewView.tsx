// L10 (2026-09-27) · L10b (2026-09-27): B10 Overview / 总览 — the landing surface.
//
// B10 structure 1:1:
//   .page-head
//   .kpi-grid          → 4 × .panel.kpi (strong + small + .trend)
//   .two-col           → .panel 执行趋势 (.spark) | .panel 系统状态
//                        (.metric-row 4 × .metric-box + .status-stack .tag)
//   .split             → .panel 最近执行 (.list / .list-item)
//                        | .panel Observer Signal Map (.graph-stage core + 6
//                          .node-dot satellites)
//
// All values are the REAL v3 snapshot projection; B5 discipline preserved:
// without a snapshot the three fact KPIs read UNKNOWN (never a fabricated 0),
// the "数据源未接入" honest indicator is present, and NO trend percentage is
// invented (the B10 demo's ↑ 18% has no real source here, so the trend row is
// omitted until a real series exists).
import * as React from 'react'
import { Plus } from 'lucide-react'
import { PageHeader } from '@/components/ui/page-header'
import { KPICard } from '@/components/dashboard/KPICard'
import { NodeGraph, type GraphNode } from '@/components/graph/node-graph'
import { Sparkline } from '@/components/ui/sparkline'
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
  const alerts = React.useMemo(() => {
    const out: { leading?: string; title: string; sub?: string; tag: string; variant: 'success' | 'warning' | 'error' | 'info' | 'muted' }[] = []
    for (const r of snap?.ci || []) {
      if (r.conclusion === 'failure' || r.conclusion === 'cancelled') {
        out.push({ leading: r.runId ?? '—', title: `${r.workflow ?? 'CI'} 失败`, sub: r.headSha ? `@ ${r.headSha.slice(0, 8)}` : undefined, tag: r.conclusion ?? 'failure', variant: 'error' })
      }
    }
    for (const r of rows) {
      if (r.state === 'FAILED' || r.state === 'BLOCKED') {
        out.push({ leading: r.id, title: '执行受阻 / 失败', sub: r.name || r.id, tag: r.state, variant: 'error' })
      }
    }
    if (tr && tr.transportState === 'OFFLINE') {
      out.push({ title: '数据源离线', sub: 'sidecar 快照不可达', tag: 'OFFLINE', variant: 'error' })
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

  // B10 `.status-stack` tags — driven by REAL transport/coverage values only.
  const stack: { text: string; variant: 'success' | 'warning' | 'info' | 'muted' }[] = [
    live
      ? { text: 'Transport LIVE', variant: 'success' }
      : { text: `Transport ${tr?.transportState || 'UNKNOWN'}`, variant: tr?.transportState === 'OFFLINE' ? 'warning' : 'muted' },
    { text: tr?.freshnessState ? `Freshness ${tr.freshnessState}` : 'Freshness UNKNOWN', variant: tr?.freshnessState === 'FRESH' ? 'info' : 'muted' },
    { text: alerts.length ? `${alerts.length} 条告警信号` : '无告警信号', variant: alerts.length ? 'warning' : 'success' },
  ]

  const taskEntries = Object.entries(snap?.tasks || {}).slice(0, 6)

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="总览"
        description="执行态势、工作流健康、观察者与审计信号整合到同一控制平面。真值来自 v3 快照投影；缺失即 UNKNOWN，不伪造。"
        actions={
          <>
            <button type="button" className="ghost-btn" disabled>导出状态</button>
            <button type="button" className="primary-btn" disabled>
              <Plus size={14} aria-hidden /> 新建执行
            </button>
          </>
        }
      />

      {/* B10 `.kpi-grid` — 4 columns; the first three are FACT KPIs (B5:
          UNKNOWN without a snapshot, never 0). The 4th reads the real
          transport word, which the CI contract requires to include LIVE. */}
      <div className="kpi-grid">
        <KPICard
          title="项目"
          value={snap ? String(snap.projects.length) : 'UNKNOWN'}
          sub={snap ? 'registry · 真实' : '数据源未接入'}
          trend={snap && snap.projects.length ? '实时投影' : undefined}
          trendTone="up"
        />
        <KPICard
          title="活跃执行"
          value={snap ? String(activeExecs) : 'UNKNOWN'}
          sub={'共 ' + (snap ? String(rows.length) : '—') + ' 条'}
          trend={snap ? '实时' : undefined}
        />
        <KPICard
          title="Token"
          value={snap ? fmtTokensSafe(tt) : 'UNKNOWN'}
          sub={'质量 ' + fmtCostQuality(tt?.costQuality)}
        />
        <KPICard
          title="数据源"
          value={live ? 'LIVE' : snap ? source.toUpperCase() : 'UNKNOWN'}
          sub={snap ? 'revision ' + String(snap.revision) : '等待数据'}
          trend={tr?.freshnessState ? '新鲜度 ' + tr.freshnessState : undefined}
          trendTone={tr?.freshnessState === 'FRESH' ? 'up' : 'warn'}
        />
      </div>

      {/* B10 `.two-col` — execution trend + system status */}
      <div className="two-col">
        <div className="panel">
          <h3>执行趋势</h3>
          {/* Honest: the v3 snapshot carries NO execution-trend series, so the
              shared Sparkline renders "无趋势数据（UNKNOWN）" rather than the
              B10 demo's fabricated sequence. */}
          <Sparkline values={[]} height={180} />
          <div className="mt-3 text-[11px] text-muted">
            {rows.length ? `${rows.length} 条执行记录（趋势序列未投影）` : '执行趋势序列未由快照投影 — 保持 UNKNOWN'}
          </div>
        </div>
        <div className="panel">
          <h3>系统状态</h3>
          <div className="metric-row">
            <div className="metric-box">
              <div className="muted text-[11px]">传输</div>
              <div className="text-[15px] font-bold tabular-nums text-ink">{tr?.transportState || 'UNKNOWN'}</div>
            </div>
            <div className="metric-box">
              <div className="muted text-[11px]">新鲜度</div>
              <div className="text-[15px] font-bold tabular-nums text-ink">{tr?.freshnessState || 'UNKNOWN'}</div>
            </div>
            <div className="metric-box">
              <div className="muted text-[11px]">覆盖</div>
              <div className="text-[15px] font-bold tabular-nums text-ink">
                {cov && cov.numerator != null ? `${cov.numerator}/${cov.denominator ?? '?'}` : 'UNKNOWN'}
              </div>
            </div>
            <div className="metric-box">
              <div className="muted text-[11px]">修订</div>
              <div className="text-[15px] font-bold tabular-nums text-ink">{snap ? String(snap.revision) : 'UNKNOWN'}</div>
            </div>
          </div>
          <div className="status-stack mt-4">
            {stack.map((s) => (
              <Badge key={s.text} variant={s.variant}>{s.text}</Badge>
            ))}
          </div>
        </div>
      </div>

      {/* B10 `.split` — recent executions + Observer Signal Map */}
      <div className="split">
        <div className="panel">
          <h3>最近执行</h3>
          {rows.length === 0 ? (
            <div className="empty py-10">
              <div className="icon" aria-hidden="true">◎</div>
              <p className="m-0 text-sm font-semibold text-ink">数据源未接入</p>
              <p className="mx-auto mt-1 max-w-md text-xs">无执行记录投影 —— 保持 UNKNOWN，不伪造执行行</p>
            </div>
          ) : (
            <div className="list">
              {rows.slice(0, 6).map((r) => (
                <div key={r.id} className="list-item">
                  <div className="min-w-0">
                    <strong className="block truncate text-[13px] font-semibold text-ink">{r.name || r.id}</strong>
                    <small className="block truncate font-mono">
                      {r.platform || 'UNKNOWN'} · {r.id}
                    </small>
                  </div>
                  <Badge variant={r.state === 'FAILED' ? 'error' : r.state === 'BLOCKED' ? 'warning' : r.state === 'COMPLETED' ? 'success' : 'info'}>
                    {r.state}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="panel">
          <h3>Observer Signal Map</h3>
          <NodeGraph core="Observer" nodes={graphNodes} className="min-h-[330px]" />
        </div>
      </div>

      {/* Honest signal panels: alerts (real failures only) + task-family counts */}
      <div className="two-col">
        <div className="panel">
          <h3>告警（真实信号）</h3>
          {alerts.length ? (
            <div className="list">
              {alerts.map((a, i) => (
                <div key={i} className="list-item">
                  <div className="min-w-0">
                    <strong className="block truncate text-[13px] font-semibold text-ink">{a.title}</strong>
                    <small className="block truncate font-mono">
                      {a.leading ? a.leading + ' · ' : ''}{a.sub || '—'}
                    </small>
                  </div>
                  <Badge variant={a.variant}>{a.tag}</Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-5 text-center text-xs text-muted">
              {snap ? '当前无告警信号（无失败 CI / 无受阻执行 / 传输在线）' : '数据源未接入 — 无法判断告警（保持 UNKNOWN，不伪造「全部正常」）'}
            </div>
          )}
        </div>
        <div className="panel">
          <h3>最近任务包</h3>
          {taskEntries.length ? (
            <div className="metric-row" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }}>
              {taskEntries.map(([family, count]) => (
                <div key={family} className="metric-box">
                  <div className="muted text-[11px]">{family}</div>
                  <div className="big-number mt-1">{count}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-5 text-center text-xs text-muted">数据源未接入 — 无任务包计数（UNKNOWN）</div>
          )}
        </div>
      </div>
    </div>
  )
}

// L10 (2026-09-27): B10 Observer lane — the READ-ONLY observer topology
// (Observer §8: topology / Agent / Workflow / Tool / MCP / Memory / Task Pack /
// abnormal nodes / running state, metrics + trend). A radial NodeGraph with a
// pulsing core + satellite nodes (B10 `.graph-stage`), a metric row, and an
// honest trend surface. Clicking a satellite opens a read-only detail Drawer;
// there are NO write/approve/retry controls anywhere on this page.
import * as React from 'react'
import { PageHeader } from '@/components/ui/page-header'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { NodeGraph, type GraphNode } from '@/components/graph/node-graph'
import { Sparkline } from '@/components/ui/sparkline'
import { StatusPill } from '@/components/ui/status'
import { Drawer } from '@/components/ui/drawer'
import type { SnapshotV3 } from '@/types'

// B10 `.metric-row` = 4 metric-box cells (transport / freshness / coverage /
// revision) — all REAL v3 values, UNKNOWN when absent.
interface MetricCell {
  label: string
  value: string
  tone?: 'success' | 'warning' | 'error' | 'muted'
}

export function ObserverView({ snap }: { snap: SnapshotV3 | null }) {
  const tr = snap?.transport
  const cov = snap?.coverage
  const [selected, setSelected] = React.useState<string | null>(null)

  // Topology nodes = the observer's own read-only projection entities. The
  // "active" state on a node reflects a REAL running execution (agent present
  // in a RUNNING/STARTING execution), never a fabricated healthy flag.
  const runningAgents = new Set(
    (snap?.executions || [])
      .filter((e) => e.state === 'RUNNING' || e.state === 'STARTING')
      .map((e) => e.agent)
      .filter((a): a is string => !!a),
  )
  const nodes: GraphNode[] = [
    { id: 'agent', label: 'Agent', state: runningAgents.size ? 'active' : 'idle' },
    { id: 'workflow', label: 'Workflow', state: 'idle' },
    { id: 'tool', label: 'Tool', state: 'idle' },
    { id: 'mcp', label: 'MCP', state: 'idle' },
    { id: 'memory', label: 'Memory', state: 'idle' },
    { id: 'taskpack', label: 'Task Pack', state: 'idle' },
  ]
  const selNode = nodes.find((n) => n.id === selected) ?? null

  const metrics: MetricCell[] = [
    {
      label: '传输状态',
      value: tr?.transportState || 'UNKNOWN',
      tone: tr?.transportState === 'LIVE' ? 'success' : tr?.transportState === 'OFFLINE' ? 'error' : 'muted',
    },
    {
      label: '新鲜度',
      value: tr?.freshnessState || 'UNKNOWN',
      tone: tr?.freshnessState === 'FRESH' ? 'success' : 'warning',
    },
    {
      label: '覆盖度',
      value:
        cov && cov.numerator != null
          ? `${cov.numerator}/${cov.denominator ?? '?'} · ${cov.scope || 'UNKNOWN'}`
          : 'UNKNOWN',
      tone: 'muted',
    },
    { label: '快照修订', value: snap ? String(snap.revision) : 'UNKNOWN', tone: 'muted' },
  ]

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Observer / 观察者"
        description="只读观测投影：拓扑 / Agent / Workflow / Tool / MCP / Memory / Task Pack / 异常节点 / 运行状态 / 指标 / 趋势。本页无任何 批准 / 拒绝 / 撤销 / 重试 操作（Observer §8 只读铁律）。"
        actions={
          <StatusPill variant={tr?.transportState === 'LIVE' ? 'success' : 'muted'}>
            {tr?.transportState || 'UNKNOWN'} · 只读
          </StatusPill>
        }
      />

      <div className="grid gap-4 xl:grid-cols-[1.35fr_0.95fr]">
        <Card className="wl-card-hover">
          <CardHeader>
            <span>观测拓扑（只读）</span>
            <span className="text-[11px] text-muted">核心 = Observer 投影 · 卫星 = 观测实体</span>
          </CardHeader>
          <CardContent>
            <NodeGraph
              core="Observer"
              nodes={nodes}
              selected={selected}
              onSelect={setSelected}
            />
          </CardContent>
        </Card>

        <div className="flex flex-col gap-4">
          <Card className="wl-card-hover">
            <CardHeader><span>指标（真实投影）</span></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                {metrics.map((m) => (
                  <div key={m.label} className="panel2 rounded-lg border border-border/62 p-3.5">
                    <div className="text-[11px] text-muted">{m.label}</div>
                    <div className="mt-1 text-lg font-bold text-ink tabular-nums">{m.value}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="wl-card-hover">
            <CardHeader><span>执行趋势</span></CardHeader>
            <CardContent>
              {/* Honest: the v3 snapshot carries NO execution-trend series.
                  Empty series -> the shared Sparkline renders "无趋势数据
                  (UNKNOWN)" — never a fabricated B10 demo sequence. */}
              <Sparkline values={[]} height={140} />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* read-only entity detail drawer */}
      <Drawer open={!!selNode} onClose={() => setSelected(null)} title={selNode ? `实体 · ${selNode.label}` : '实体详情'}>
        {selNode ? (
          <div className="flex flex-col gap-3">
            <StatusPill variant={selNode.state === 'active' ? 'success' : selNode.state === 'error' ? 'error' : 'muted'}>
              {selNode.state === 'active' ? '运行中' : selNode.state === 'error' ? '异常' : '空闲'}
            </StatusPill>
            <p className="text-xs leading-relaxed text-muted">
              该实体为 Observer 只读观测投影。{selNode.state === 'active' ? '当前存在真实运行中的执行（agent 维度命中）。' : '未观测到运行中的执行。'}
              无任何操作入口 — 观测不等于控制。
            </p>
          </div>
        ) : null}
      </Drawer>
    </div>
  )
}

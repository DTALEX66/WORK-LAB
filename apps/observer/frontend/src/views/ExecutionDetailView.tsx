// L10 (2026-09-27): B10 Execution Detail lane — read-only detail surface
// for a single execution. The execution list + every field value are the
// REAL v3 executions[] projection; selecting an execution opens its detail.
// No write actions (Observer §8 read-only).
import * as React from 'react'
import { PageHeader } from '@/components/ui/page-header'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { ListView } from '@/components/ui/list'
import { StatusPill } from '@/components/ui/status'
import { UnknownState } from '@/components/ui/states'
import { Badge } from '@/components/ui/badge'
import type { SnapshotV3, Execution, ExecutionState } from '@/types'
import { stateTone } from '@/lib/api'

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

function DetailRow({ k, v }: { k: string; v: React.ReactNode }) {
  const empty = v == null || v === ''
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border/40 last:border-0 py-2">
      <span className="text-[11px] text-muted">{k}</span>
      <span className="min-w-0 truncate text-right text-[11px] font-mono text-ink">{empty ? 'UNKNOWN' : v}</span>
    </div>
  )
}

export function ExecutionDetailView({ snap }: { snap: SnapshotV3 | null }) {
  const exs: Execution[] = snap?.executions || []
  const [selId, setSelId] = React.useState<string | null>(exs[0]?.executionId ?? null)
  const sel = exs.find((e) => e.executionId === selId) ?? exs[0] ?? null

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Execution Detail / 执行详情"
        description="单条执行的只读详情投影（executions[]）。选中左侧执行查看时间 / 主体 / 资源 / 结果 / 来源。"
      />

      {exs.length === 0 ? (
        <Card>
          <CardContent>
            <UnknownState
              title="无执行记录"
              description="当前快照未携带 executions[] 投影。Observer 保持 UNKNOWN，不伪造执行历史。"
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
          <Card>
            <CardHeader>
              <span>执行列表</span>
              <span className="text-[11px] text-muted">{exs.length} 条</span>
            </CardHeader>
            <CardContent className="p-3">
              <ListView
                items={exs.map((e) => ({
                  leading: e.executionId,
                  title: e.agent || 'UNKNOWN',
                  sub: STATE_TEXT[e.state] || e.state,
                  state: { text: STATE_TEXT[e.state] || e.state, variant: toneVariant(stateTone(e.state)) },
                }))}
              />
              <p className="mt-3 text-[10px] text-muted">
                点击画布节点或在本页选择执行以切换详情（当前：
                <span className="font-mono text-ink">{sel?.executionId ?? '—'}</span>）
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <span>详情 · {sel ? sel.executionId : 'UNKNOWN'}</span>
              {sel ? (
                <StatusPill variant={toneVariant(stateTone(sel.state))}>
                  {STATE_TEXT[sel.state] || sel.state}
                </StatusPill>
              ) : null}
            </CardHeader>
            <CardContent>
              {sel ? (
                <div>
                  <DetailRow k="状态" v={STATE_TEXT[sel.state] || sel.state} />
                  <DetailRow k="状态质量" v={sel.stateQuality || 'UNKNOWN'} />
                  <DetailRow k="主体（Agent）" v={sel.agent || 'UNKNOWN'} />
                  <DetailRow k="锚定项目" v={sel.anchorProjectId || 'UNKNOWN'} />
                  <DetailRow k="会话" v={sel.sessionId || 'UNKNOWN'} />
                  <DetailRow k="工作区" v={sel.workingArea || 'UNKNOWN'} />
                  <DetailRow k="来源引用" v={sel.sourceRef || 'UNKNOWN'} />
                  <div className="mt-3 flex items-center gap-2 text-[11px] text-muted">
                    <Badge variant="muted">只读投影</Badge>
                    无 重试 / 撤销 / 重放 操作（Observer §8 只读铁律）
                  </div>
                </div>
              ) : (
                <UnknownState title="执行数据未知" />
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

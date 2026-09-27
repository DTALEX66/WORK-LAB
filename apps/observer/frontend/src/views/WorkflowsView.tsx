// L10 (2026-09-27): B10 Workflows lane — the workflow list surface.
// The v3 snapshot carries NO workflows[] array today, so this page is the
// honest B10 structure (toolbar + table + state pills) with a real empty
// state: no fabricated workflow rows. The toolbar/search/filter are fully
// functional against whatever a future workflows[] projection provides.
import * as React from 'react'
import { Plus, Search } from 'lucide-react'
import { PageHeader } from '@/components/ui/page-header'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input, SearchInput, Select } from '@/components/ui/input'
import { StatusPill } from '@/components/ui/status'
import { DataTable, type DataTableColumn } from '@/components/ui/table'
import { UnknownState } from '@/components/ui/states'
import { Tooltip } from '@/components/ui/tooltip'
import type { SnapshotV3 } from '@/types'

export interface WorkflowRow {
  id: string
  name: string
  owner?: string
  version?: string
  lastRunAt?: string
  state?: string
}

const STATE_PILLS: { value: string; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'active', label: '活跃' },
  { value: 'draft', label: '草稿' },
  { value: 'archived', label: '已归档' },
]

export function WorkflowsView({ snap }: { snap: SnapshotV3 | null }) {
  // Honest source: a future workflows[] projection (absent today -> []).
  const workflows: WorkflowRow[] =
    Array.isArray((snap as unknown as { workflows?: WorkflowRow[] })?.workflows)
      ? (snap as unknown as { workflows: WorkflowRow[] }).workflows
      : []
  const [query, setQuery] = React.useState('')
  const [state, setState] = React.useState('all')

  const filtered = workflows.filter((w) => {
    if (state !== 'all' && w.state !== state) return false
    if (query && !(w.name + w.owner + w.id).toLowerCase().includes(query.toLowerCase())) return false
    return true
  })

  const columns: DataTableColumn<WorkflowRow>[] = [
    {
      key: 'name',
      header: '工作流',
      cell: (w) => (
        <div>
          <div className="font-medium text-ink">{w.name}</div>
          <div className="font-mono text-[10px] text-muted">{w.id}</div>
        </div>
      ),
    },
    {
      key: 'state',
      header: '状态',
      cell: (w) => (
        <StatusPill variant={w.state === 'active' ? 'success' : w.state === 'archived' ? 'muted' : 'info'}>
          {w.state ?? 'UNKNOWN'}
        </StatusPill>
      ),
    },
    { key: 'owner', header: '负责人', cell: (w) => <span className="text-muted">{w.owner || 'UNKNOWN'}</span> },
    {
      key: 'version',
      header: '版本',
      cell: (w) => <span className="font-mono text-muted">{w.version ?? 'UNKNOWN'}</span>,
    },
    {
      key: 'lastRunAt',
      header: '最后执行',
      cell: (w) => (
        <span className="text-muted">
          {w.lastRunAt ? new Date(w.lastRunAt).toLocaleString() : 'UNKNOWN'}
        </span>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Workflows / 工作流"
        description="受管客户端（Hermes · Codex · DSH · GitHub · Open Design · Open Human）的工作流清单。真值来自 v3 快照投影；契约缺失时保持 UNKNOWN。"
        actions={
          <Tooltip text="工作流契约（workflows[]）未接入 — 无真实创建入口">
            <span>
              <Button disabled iconLeft={Plus} variant="primary">
                新建工作流
              </Button>
            </span>
          </Tooltip>
        }
      />

      <Card>
        <div className="flex flex-wrap items-center gap-2 p-3.5 border-b border-border/60">
          <SearchInput
            placeholder="搜索工作流 / 负责人 / ID…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="搜索工作流"
            className="w-64 h-9"
          />
          <Select
            value={state}
            onChange={(e) => setState(e.target.value)}
            aria-label="按状态筛选"
            className="w-32 h-9"
          >
            {STATE_PILLS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </Select>
          <span className="ml-auto text-[11px] text-muted tabular-nums">
            {workflows.length ? `${filtered.length} / ${workflows.length} 条` : '契约未投影'}
          </span>
        </div>
        <CardContent className="p-0">
          {workflows.length === 0 ? (
            <UnknownState
              title="工作流数据未知"
              description="当前 v3 快照未携带 workflows[] 契约。搜索 / 筛选 / 状态标签结构已就绪；工作流真值将由后续契约投影至本页，Observer 保持 UNKNOWN，不伪造工作流行。"
            />
          ) : (
            <DataTable
              columns={columns}
              rows={filtered}
              rowKey={(w) => w.id}
              empty={
                <div className="py-6 text-center text-xs text-muted">
                  <Search size={16} className="mx-auto mb-2 opacity-60" aria-hidden />
                  该筛选条件下无工作流
                </div>
              }
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}

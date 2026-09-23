// UI_VIEWS (20260921): Task Packs lane — projects the REAL task-family counts
// (snap.tasks: Record<string, number>) and, when present, the plan's task list
// (snap.workspace.plan.tasks). Honest discipline: counts are shown only when
// the backend carried them; an empty tasks map renders an EmptyState, never a
// fabricated "N task packs running".
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/ui/states'

export function TaskPacksView({ snap }: { snap: any }) {
  const tasks: Record<string, number> = snap?.tasks ?? {}
  const planTasks: { taskId?: string; [k: string]: unknown }[] | undefined =
    snap?.workspace?.plan?.tasks && Array.isArray(snap.workspace.plan.tasks)
      ? snap.workspace.plan.tasks
      : undefined
  const total = Object.values(tasks).reduce((a, b) => a + (b || 0), 0)
  const hasCounts = Object.keys(tasks).length > 0

  return (
    <div className="flex flex-col gap-4 overflow-auto p-4">
      <Card>
        <CardHeader>
          <span>任务包 · 家族计数（真实投影）</span>
          <span className="text-[11px] text-muted">{hasCounts ? `合计 ${total} 项` : '无计数数据'}</span>
        </CardHeader>
        <CardContent>
          {!hasCounts ? (
            <EmptyState
              title="无任务包计数"
              description="当前快照未携带 tasks 家族计数（snap.tasks 为空）。Observer 保持 UNKNOWN，不伪造任务包状态。"
            />
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {Object.entries(tasks).map(([family, count]) => (
                <div key={family} className="panel2 p-3">
                  <div className="text-[11px] text-muted">{family}</div>
                  <div className="text-2xl font-semibold text-secondary tabular-nums">{count}</div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><span>计划任务明细</span></CardHeader>
        <CardContent>
          {planTasks && planTasks.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[11px]">
                <thead>
                  <tr className="border-b border-border text-muted">
                    <th className="py-2 pr-3 font-medium">任务 ID</th>
                    <th className="py-2 font-medium">属性</th>
                  </tr>
                </thead>
                <tbody>
                  {planTasks.map((t, i) => {
                    const props = Object.entries(t).filter(([k]) => k !== 'taskId')
                    return (
                      <tr key={i} className="border-b border-border/40 last:border-0">
                        <td className="py-2 pr-3 font-mono text-secondary">{t.taskId ?? `task-${i + 1}`}</td>
                        <td className="py-2 text-muted">
                          {props.length ? props.map(([k, v]) => `${k}=${String(v)}`).join(' · ') : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-4 text-center text-xs text-muted">
              当前快照未携带计划任务明细（workspace.plan.tasks 缺失）。
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><span>原则</span></CardHeader>
        <CardContent className="text-xs text-muted">
          任务包计数来自后端真实投影（snap.tasks / workspace.plan.tasks）。
          缺失即 UNKNOWN，不伪造任务包运行态，不新增任务操作入口。
        </CardContent>
      </Card>
    </div>
  )
}

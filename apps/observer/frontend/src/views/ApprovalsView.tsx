// UI_VIEWS (20260921): Approvals lane — the backend snapshot has NO
// approvals[] array. The only real approval data that can exist today is
// snap.workspace.plan.approvals (when the plan carries it). Everything else
// must stay UNKNOWN: this view states the projection gap explicitly and
// renders ONLY what is actually present. No approve/deny buttons (read-only).
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { UnknownState } from '@/components/ui/states'

function approvalVariant(state: string | undefined): 'success' | 'warning' | 'error' | 'muted' {
  const s = (state ?? '').toLowerCase()
  if (s === 'approved' || s === 'granted') return 'success'
  if (s === 'pending' || s === 'requested' || s === 'in_review') return 'warning'
  if (s === 'denied' || s === 'revoked' || s === 'rejected') return 'error'
  return 'muted'
}

export function ApprovalsView({ snap }: { snap: any }) {
  const plan = snap?.workspace?.plan
  const approvals: { state?: string; [k: string]: unknown }[] | undefined =
    plan?.approvals && Array.isArray(plan.approvals) ? plan.approvals : undefined

  return (
    <div className="flex flex-col gap-4 overflow-auto p-4">
      <Card>
        <CardHeader>
          <span>审批中心（只读投影）</span>
          <span className="text-[11px] text-muted">
            {approvals?.length ? `${approvals.length} 项审批记录` : '无审批数据'}
          </span>
        </CardHeader>
        <CardContent>
          {approvals && approvals.length > 0 ? (
            <ul className="flex flex-col gap-2">
              {approvals.map((a, i) => (
                <li key={i} className="panel2 p-3 flex items-center justify-between gap-3">
                  <div className="text-[11px] text-ink min-w-0">
                    <span className="font-mono">
                      {String(a.taskId ?? a.id ?? `approval-${i + 1}`)}
                    </span>
                    {a.reason ? <span className="ml-2 text-muted">{String(a.reason)}</span> : null}
                  </div>
                  <Badge variant={approvalVariant(a.state)}>
                    {a.state ?? 'UNKNOWN'}
                  </Badge>
                </li>
              ))}
            </ul>
          ) : (
            <UnknownState
              title="审批数据未知"
              description="当前快照未携带审批契约（无 approvals[] 数组）。审批数据将由后续审批契约投影至本页面；Observer 保持 UNKNOWN，不伪造已审批状态，也不提供审批操作。"
            />
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><span>原则</span></CardHeader>
        <CardContent className="text-xs text-muted">
          审批真值来自后端审批契约（workspace.plan.approvals）。本视图只读：
          不渲染批准 / 拒绝 / 撤销按钮，不构成第二个审批 Authority。
        </CardContent>
      </Card>
    </div>
  )
}

import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { AgentRow } from '@/lib/api'
import { stateTone, fmtTokens, fmtCostQuality } from '@/lib/api'

const STATE_TEXT: Record<string, string> = {
  RUNNING: '运行中', STARTING: '启动中', WAITING_USER: '待用户', WAITING_APPROVAL: '待审批',
  BLOCKED: '受阻', COMPLETED: '完成', FAILED: '失败', UNKNOWN: '未知',
}

// U07: execution rows are the REAL v3 `executions[]` joined with their anchor
// project (platform + token truth). No fabricated cost/usage percentages —
// costQuality is the backend label, tokens null render UNKNOWN.
export function ExecutionTable({ rows, hasData }: { rows: AgentRow[]; hasData: boolean }) {
  return (
    <Card>
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border text-sm font-medium">
        <span>执行</span>
        <span className="text-[11px] text-zinc-500">{hasData ? rows.length + ' 条 · 真实' : '等待数据'}</span>
      </div>
      <div className="p-0 overflow-x-auto">
        {rows.length === 0 ? (
          <div className="p-8 text-center text-zinc-500 text-xs">
            {hasData ? '暂无执行记录（UNKNOWN）' : '数据源未接入 · 保持 UNKNOWN'}
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-panel2 text-left text-[11px] text-zinc-500">
                <th className="px-4 py-2 font-medium">执行</th>
                <th className="px-3 py-2 font-medium">状态</th>
                <th className="px-3 py-2 font-medium">平台</th>
                <th className="px-3 py-2 font-medium">项目</th>
                <th className="px-3 py-2 font-medium">Token</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 20).map((a) => (
                <tr key={a.id} className="border-t border-border hover:bg-white/[0.03]">
                  <td className="px-4 py-2.5">
                    <div className="font-medium" style={{ fontSize: 12 }}>{a.name || a.id}</div>
                    <div className="text-[10px] text-zinc-600 font-mono">{a.id}</div>
                  </td>
                  <td className="px-3 py-2.5">
                    <Badge variant={stateTone(a.state) === 'running' ? 'success' : stateTone(a.state) === 'pending' || stateTone(a.state) === 'blocked' ? 'warning' : stateTone(a.state) === 'failed' ? 'error' : 'muted'}>
                      {STATE_TEXT[a.state] || a.state}
                    </Badge>
                  </td>
                  <td className="px-3 py-2.5 text-zinc-400">{a.platform || 'UNKNOWN'}</td>
                  <td className="px-3 py-2.5 text-zinc-300">{a.anchorProjectId || 'UNKNOWN'}</td>
                  <td className="px-3 py-2.5 tabular-nums text-zinc-300" title="成本质量（后端权威）">
                    {fmtTokens(a.totalTokens)} <span className="text-[10px] text-zinc-600">{fmtCostQuality(a.costQuality)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Card>
  )
}

import { useMemo } from 'react'
import type { Agent } from '@/types'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { fmtTokens, fmtCost } from '@/lib/api'

const statusVariant = { running: 'success', pending: 'warning', failed: 'error', idle: 'muted' } as const
const statusDot = { running: '#00d084', pending: '#ffb020', failed: '#ff4d4f', idle: '#71717a' }
const statusText = { running: '运行中', pending: '待处理', failed: '失败', idle: '空闲' } as const

export function AgentTable({ agents }: { agents: Agent[] }) {
  const rows = useMemo(() => agents, [agents])
  return (
    <Card>
      <CardHeader>
        <span>Agent 舰队</span>
        <span className="text-[11px] text-zinc-500">{agents.length} 个执行 · 真实数据</span>
      </CardHeader>
      <CardContent className="p-0 overflow-x-auto">
        {rows.length === 0 ? (
          <div className="p-8 text-center text-zinc-500 text-xs">暂无执行 · 等待数据源</div>
        ) : (
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-panel2 text-left text-[11px] text-zinc-500">
              <th className="px-4 py-2 font-medium">Agent</th>
              <th className="px-3 py-2 font-medium">状态</th>
              <th className="px-3 py-2 font-medium">运行时</th>
              <th className="px-3 py-2 font-medium">项目</th>
              <th className="px-3 py-2 font-medium">Token</th>
              <th className="px-3 py-2 font-medium">成本</th>
              <th className="px-3 py-2 font-medium">用量</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.id} className="border-t border-border hover:bg-white/[0.03] transition-colors">
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2.5">
                    <span className="w-7 h-7 rounded-md flex items-center justify-center text-[10px] font-bold" style={{ background: 'rgba(124,108,240,0.12)', color: '#7c6cf0' }}>
                      {a.name.slice(-2).toUpperCase()}
                    </span>
                    <div>
                      <div className="font-medium" style={{ fontSize: 12 }}>{a.name}</div>
                      <div className="text-[10px] text-zinc-600 font-mono">{a.id}</div>
                    </div>
                  </div>
                </td>
                <td className="px-3 py-2.5">
                  <Badge variant={statusVariant[a.status]}><span className="w-1.5 h-1.5 rounded-full" style={{ background: statusDot[a.status] }} />{statusText[a.status]}</Badge>
                </td>
                <td className="px-3 py-2.5 text-zinc-400">{a.runtime}</td>
                <td className="px-3 py-2.5 text-zinc-300">{a.task}</td>
                <td className="px-3 py-2.5 text-zinc-300 tabular-nums">{fmtTokens(a.tokens)}</td>
                <td className="px-3 py-2.5 tabular-nums" style={{ color: '#00d4ff' }}>{fmtCost(a.cost)}</td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-2">
                    <div className="w-14 h-1 rounded-full bg-zinc-700/60 overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: a.usagePct + '%', background: a.usagePct > 85 ? '#ff4d4f' : '#00d084' }} />
                    </div>
                    <span className="text-[10px] text-zinc-500 tabular-nums">{a.usagePct}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        )}
      </CardContent>
    </Card>
  )
}

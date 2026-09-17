import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Cell, PieChart, Pie, LineChart, Line } from 'recharts'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import type { CostPoint } from '@/types'
import { fmtCost, fmtTokens } from '@/lib/api'

export function CostPanel({ costs, tokenTotal, tokenIn, tokenOut, costTrend }: { costs: CostPoint[]; tokenTotal: number | null; tokenIn: number | null; tokenOut: number | null; costTrend: number[] }) {
  const total = tokenTotal != null && tokenTotal > 0 ? tokenTotal : 1
  const tokenDist = [
    { name: '输入', value: tokenIn == null ? null : Math.round((tokenIn / total) * 100), color: '#00d4ff' },
    { name: '输出', value: tokenOut == null ? null : Math.round((tokenOut / total) * 100), color: '#7c6cf0' },
  ]
  const trendData = costTrend.length ? costTrend.map((v, i) => ({ i, v })) : []
  return (
    <div className="flex flex-col gap-3">
      <Card>
        <CardHeader><span>成本走势</span><span className="text-[11px] text-zinc-500">6 小时 · 真实</span></CardHeader>
        <CardContent>
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={120}>
              <LineChart data={trendData} margin={{ top: 4, right: 0, left: -22, bottom: 0 }}>
                <XAxis dataKey="i" tick={false} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 9, fill: '#71717a' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#161b22', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6, fontSize: 11 }} />
                <Line type="monotone" dataKey="v" stroke="#00d4ff" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <div className="text-center text-[11px] text-zinc-600 py-8">成本走势数据积累中…</div>}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><span>项目成本分布</span><span className="text-[11px] text-zinc-500">估算 · 人民币</span></CardHeader>
        <CardContent className="flex flex-col gap-2">
          {costs.length > 0 ? costs.map((c) => {
            const validCosts = costs.map((x) => x.cost).filter((v): v is number => v != null)
            const maxCost = validCosts.length ? Math.max(...validCosts, 0.01) : 0.01
            const pct = c.cost == null ? 0 : (c.cost / maxCost) * 100
            return (
              <div key={c.date} className="flex items-center gap-2">
                <span className="w-24 shrink-0 text-[10px] text-zinc-500 truncate text-right">{c.date}</span>
                <div className="flex-1 h-3 rounded-sm bg-zinc-700/40 overflow-hidden">
                  {c.cost != null && c.cost > 0 && <div className="h-full rounded-sm" style={{ width: Math.max(pct, 2) + '%', background: '#00d4ff' }} />}
                </div>
                <span className="w-16 shrink-0 text-[10px] tabular-nums text-right" style={{ color: c.cost != null && c.cost > 0 ? '#00d4ff' : '#71717a' }}>{c.cost != null && c.cost > 0 ? fmtCost(c.cost) : 'UNKNOWN'}</span>
              </div>
            )
          }) : <div className="text-center text-[11px] text-zinc-600 py-4">暂无项目成本数据</div>}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><span>Token 分布</span></CardHeader>
        <CardContent className="flex items-center gap-3">
          <ResponsiveContainer width="45%" height={100}>
            <PieChart>
              <Pie data={tokenDist} dataKey="value" innerRadius={28} outerRadius={42} paddingAngle={2} stroke="none">
                {tokenDist.map((d, i) => (<Cell key={i} fill={d.color} />))}
              </Pie>
              <Tooltip contentStyle={{ background: '#161b22', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6, fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex-1 flex flex-col gap-1">
            {tokenDist.map((d) => (<div key={d.name} className="flex items-center justify-between text-[11px]"><span className="flex items-center gap-1.5 text-zinc-400"><span className="w-2 h-2 rounded-full" style={{ background: d.color }} />{d.name}</span><span className="tabular-nums text-zinc-200">{d.value}%</span></div>))}
            <div className="flex items-center justify-between text-[11px] mt-1"><span className="text-zinc-500">总计</span><span className="tabular-nums text-zinc-200">{fmtTokens(tokenTotal)}</span></div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

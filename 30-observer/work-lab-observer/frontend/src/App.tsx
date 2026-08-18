import { useState, useEffect } from 'react'
import { Bot, ListTodo, Coins, DollarSign } from 'lucide-react'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopStatusBar } from '@/components/layout/TopStatusBar'
import { KPICard } from '@/components/dashboard/KPICard'
import { CostPanel } from '@/components/dashboard/CostPanel'
import { ResourceMonitor } from '@/components/dashboard/ResourceMonitor'
import { AgentsView, ExecutionsView, ModelsView, MemoryView, ToolsView, MonitoringView, SettingsView } from '@/views/Views'
import { fetchSnapshot, executionsToAgents, snapshotToServices, snapshotToTimeline, snapshotToCosts, estimateCost, fmtTokens, fmtCost, promRange, fetchResources, type LiveSnapshot, type SysResources } from '@/lib/api'
import type { Agent, TimelineEvent, ServiceHealth, CostPoint } from '@/types'

export default function App() {
  const [view, setView] = useState(0)
  const [snap, setSnap] = useState<LiveSnapshot | null>(null)
  const [agents, setAgents] = useState<Agent[]>([])
  const [services, setServices] = useState<ServiceHealth[]>([])
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [costs, setCosts] = useState<CostPoint[]>([])
  const [tokenTotal, setTokenTotal] = useState(0)
  const [tokenIn, setTokenIn] = useState(0)
  const [tokenOut, setTokenOut] = useState(0)
  const [live, setLive] = useState(false)
  const [resources, setResources] = useState<SysResources | null>(null)
  const [tokenTrend, setTokenTrend] = useState<number[]>([])
  const [costTrend, setCostTrend] = useState<number[]>([])

  // real time-series from Prometheus (KPI sparklines + cost line + resources)
  useEffect(() => {
    let cancelled = false
    const loadProm = async () => {
      const [res, tt, ct] = await Promise.all([
        fetchResources(),
        promRange('wlobs_usage_tokens{kind="total"}', 360),
        promRange('wlobs_cost_estimate', 360),
      ])
      if (cancelled) return
      if (res) setResources(res)
      if (tt.length) setTokenTrend(tt)
      if (ct.length) setCostTrend(ct)
    }
    loadProm()
    const t = setInterval(loadProm, 15000)
    return () => { cancelled = true; clearInterval(t) }
  }, [])

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      const s = await fetchSnapshot()
      if (cancelled) return
      if (s) {
        setLive(true)
        setSnap(s)
        setAgents(executionsToAgents(s))
        setServices(snapshotToServices(s))
        setTimeline(snapshotToTimeline(s))
        setCosts(snapshotToCosts(s))
        setTokenTotal(s.tokenSummary?.totalTokens || 0)
        setTokenIn(s.tokenSummary?.inputTokens || 0)
        setTokenOut(s.tokenSummary?.outputTokens || 0)
      } else setLive(false)
    }
    load()
    const t = setInterval(load, 10000)
    return () => { cancelled = true; clearInterval(t) }
  }, [])

  const running = agents.filter((a) => a.status === 'running').length
  const cost = estimateCost(tokenIn, tokenOut)
  const sparkTok = tokenTrend.length > 1 ? tokenTrend : []
  const sparkCost = costTrend.length > 1 ? costTrend : []
  // real trend % from prom series (first -> last)
  const tokTrend = tokenTrend.length > 1 ? Math.round(((tokenTrend[tokenTrend.length - 1] - tokenTrend[0]) / (tokenTrend[0] || 1)) * 100) : undefined
  const costTrendPct = costTrend.length > 1 ? Math.round(((costTrend[costTrend.length - 1] - costTrend[0]) / (costTrend[0] || 1)) * 100) : undefined

  const overview = (
    <div className="flex flex-col gap-4 min-h-0">
      <div className="grid grid-cols-4 gap-4">
        <KPICard icon={Bot} label="活跃 Agent" value={String(running)} color="#00d4ff" />
        <KPICard icon={ListTodo} label="执行中" value={String(agents.length)} color="#7c6cf0" />
        <KPICard icon={Coins} label="Token 用量" value={fmtTokens(tokenTotal)} trend={tokTrend} spark={sparkTok} color="#00d084" />
        <KPICard icon={DollarSign} label="估算成本" value={fmtCost(cost)} trend={costTrendPct} spark={sparkCost} color="#ffb020" />
      </div>
      <div className="grid grid-cols-[1fr_320px] gap-4 min-h-0 flex-1">
        <div className="flex flex-col gap-4 min-h-0">
          <div className="flex-1 min-h-0 overflow-auto"><AgentsView agents={agents} snap={snap} /></div>
        </div>
        <div className="flex flex-col gap-4 overflow-auto">
          <CostPanel costs={costs} tokenTotal={tokenTotal} tokenIn={tokenIn} tokenOut={tokenOut} costTrend={costTrend} />
          <ResourceMonitor resources={resources} />
        </div>
      </div>
    </div>
  )

  const views = [
    overview,
    <AgentsView key="a" agents={agents} snap={snap} />,
    <ExecutionsView key="e" timeline={timeline} snap={snap} />,
    <ModelsView key="m" tokenIn={tokenIn} tokenOut={tokenOut} tokenTotal={tokenTotal} snap={snap} />,
    <MemoryView key="me" snap={snap} />,
    <ToolsView key="t" snap={snap} />,
    <MonitoringView key="mo" services={services} snap={snap} />,
    <SettingsView key="s" live={live} snap={snap} />,
  ]

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar active={view} onSelect={setView} />
      <div className="flex-1 flex flex-col min-w-0">
        <TopStatusBar services={services} />
        <div className="flex-1 p-4 overflow-auto min-h-0">
          <div className="flex items-center gap-2 text-[11px] text-zinc-500 mb-4">
            <span className={"w-1.5 h-1.5 rounded-full " + (live ? 'bg-success status-pulse' : 'bg-warning')} />
            {live ? '已接入真实数据 · sidecar :61867 · 10s 刷新' : '数据源离线'}
          </div>
          {views[view]}
        </div>
      </div>
    </div>
  )
}

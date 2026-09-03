import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { AgentTable } from '@/components/dashboard/AgentTable'
import { Timeline } from '@/components/dashboard/Timeline'
import { Badge } from '@/components/ui/badge'
import type { Agent, TimelineEvent, ServiceHealth, CostPoint } from '@/types'
import { fmtTokens, fmtCost, estimateCost } from '@/lib/api'

function Row({ k, v }: { k: string; v: any }) {
  return <div className="flex items-center justify-between py-1 border-b border-border/40 last:border-0"><span className="text-[11px] text-zinc-500">{k}</span><span className="text-[11px] text-zinc-200 truncate ml-3 text-right">{v === null || v === undefined || v === '' ? '—' : String(v)}</span></div>
}

// ---------- 智能体 ----------
export function AgentsView({ agents, snap }: { agents: Agent[]; snap: any }) {
  const projects = snap?.projects || []
  return (
    <div className="flex flex-col gap-4">
      <AgentTable agents={agents} />
      <Card>
        <CardHeader><span>项目平台</span><span className="text-[11px] text-zinc-500">{projects.length} 个项目</span></CardHeader>
        <CardContent className="grid grid-cols-2 gap-3">
          {projects.map((p: any) => (
            <div key={p.projectId} className="panel2 p-3 rounded">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium">{p.displayName || p.projectId}</span>
                <Badge variant={p.activityState === 'ACTIVE' ? 'success' : 'muted'}>{p.activityState || '未知'}</Badge>
              </div>
              <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] text-zinc-400">
                <span>平台: {p.agentPlatform || '—'}</span>
                <span>执行: {p.activeExecutionCount || 0}</span>
                <span>Token: {fmtTokens(Number(p.token?.totalTokens) || 0)}</span>
                <span>成本: {fmtCost(estimateCost(Number(p.token?.inputTokens) || 0, Number(p.token?.outputTokens) || 0))}</span>
              </div>
              <div className="mt-2 flex items-center gap-2 text-[10px] text-zinc-600">
                <span className="font-mono">{p.git?.branch || '—'}@{p.git?.localSha?.slice(0, 7) || '—'}</span>
                {p.git?.dirtyCount ? <Badge variant="warning">脏 {p.git.dirtyCount}</Badge> : <Badge variant="success">干净</Badge>}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

// ---------- 执行 ----------
export function ExecutionsView({ timeline, snap }: { timeline: TimelineEvent[]; snap: any }) {
  const exs = snap?.executions || []
  const transport = snap?.transport || {}
  return (
    <div className="flex flex-col gap-4">
      <Timeline events={timeline} />
      <Card>
        <CardHeader><span>执行详情</span><span className="text-[11px] text-zinc-500">{exs.length} 个执行</span></CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-xs">
            <thead><tr className="bg-panel2 text-left text-[11px] text-zinc-500">
              <th className="px-4 py-2 font-medium">执行 ID</th><th className="px-3 py-2 font-medium">Agent</th><th className="px-3 py-2 font-medium">状态</th><th className="px-3 py-2 font-medium">项目</th><th className="px-3 py-2 font-medium">会话</th><th className="px-3 py-2 font-medium">工作区</th>
            </tr></thead>
            <tbody>
              {exs.map((e: any) => (
                <tr key={e.executionId} className="border-t border-border">
                  <td className="px-4 py-2 font-mono text-zinc-400">{e.executionId}</td>
                  <td className="px-3 py-2">{e.agent}</td>
                  <td className="px-3 py-2"><Badge variant={String(e.state).includes('RUN') ? 'success' : 'muted'}>{e.state}</Badge></td>
                  <td className="px-3 py-2 text-zinc-300">{e.anchorProjectId}</td>
                  <td className="px-3 py-2 font-mono text-[10px] text-zinc-500">{e.sessionId}</td>
                  <td className="px-3 py-2 font-mono text-[10px] text-zinc-500">{e.workingArea}</td>
                </tr>
              ))}
              {exs.length === 0 && <tr><td colSpan={6} className="px-4 py-6 text-center text-zinc-500 text-[11px]">暂无执行</td></tr>}
            </tbody>
          </table>
        </CardContent>
      </Card>
      <div className="grid grid-cols-2 gap-4">
        <Card><CardHeader><span>事件流</span></CardHeader><CardContent>
          <Row k="传输状态" v={transport.transportState || '—'} /><Row k="新鲜度" v={transport.freshnessState || '—'} />
          <Row k="事件流连接" v={transport.eventStreamConnected ? '已连接' : '未连接'} />
          <Row k="最后心跳" v={transport.lastHeartbeatAt ? new Date(transport.lastHeartbeatAt).toLocaleTimeString() : '—'} />
          <Row k="写入水位" v={transport.writerWatermarkAt ? new Date(transport.writerWatermarkAt).toLocaleTimeString() : '—'} />
        </CardContent></Card>
        <Card><CardHeader><span>快照信息</span></CardHeader><CardContent>
          <Row k="修订号" v={snap?.revision || '—'} /><Row k="Schema" v={snap?.schemaVersion || '—'} />
          <Row k="生成时间" v={snap?.generatedAt ? new Date(snap.generatedAt).toLocaleString() : '—'} />
          <Row k="数据水位" v={snap?.sourceWatermark || '—'} />
        </CardContent></Card>
      </div>
    </div>
  )
}

// ---------- 模型 ----------
export function ModelsView({ tokenIn, tokenOut, tokenTotal, snap }: { tokenIn: number | null; tokenOut: number | null; tokenTotal: number | null; snap: any }) {
  // WLR-130: unknown values render as UNKNOWN, never 0
  const dist = [
    { name: '输入 Token', value: tokenIn, color: '#00d4ff' },
    { name: '输出 Token', value: tokenOut, color: '#7c6cf0' },
  ]
  const max = Math.max(tokenIn ?? 0, tokenOut ?? 0, 1)
  const projects = snap?.projects || []
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader><span>模型用量</span><span className="text-[11px] text-zinc-500">估算</span></CardHeader>
        <CardContent className="flex flex-col gap-4">
          {dist.map((d) => (
            <div key={d.name}>
              <div className="flex justify-between text-xs mb-1"><span className="flex items-center gap-1.5 text-zinc-300"><span className="w-2 h-2 rounded-full" style={{ background: d.color }} />{d.name}</span><span className="tabular-nums">{fmtTokens(d.value)}</span></div>
              <div className="h-2 rounded-full bg-zinc-700/50 overflow-hidden"><div className="h-full rounded-full" style={{ width: ((d.value ?? 0) / max) * 100 + '%', background: d.color }} /></div>
            </div>
          ))}
          <div className="flex justify-between text-xs text-zinc-400"><span>总计</span><span className="tabular-nums text-zinc-200">{fmtTokens(tokenTotal)}</span></div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><span>项目 Token 明细</span></CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-xs">
            <thead><tr className="bg-panel2 text-left text-[11px] text-zinc-500"><th className="px-4 py-2 font-medium">项目</th><th className="px-3 py-2 font-medium">输入</th><th className="px-3 py-2 font-medium">输出</th><th className="px-3 py-2 font-medium">总计</th><th className="px-3 py-2 font-medium">成本</th></tr></thead>
            <tbody>
              {projects.map((p: any) => {
                const t = p.token || {}
                const inp = Number(t.inputTokens) || 0
                const out = Number(t.outputTokens) || 0
                return (
                  <tr key={p.projectId} className="border-t border-border">
                    <td className="px-4 py-2">{p.displayName || p.projectId}</td>
                    <td className="px-3 py-2 tabular-nums text-zinc-300">{fmtTokens(inp)}</td>
                    <td className="px-3 py-2 tabular-nums text-zinc-300">{fmtTokens(out)}</td>
                    <td className="px-3 py-2 tabular-nums">{fmtTokens(inp + out)}</td>
                    <td className="px-3 py-2 tabular-nums" style={{ color: '#00d4ff' }}>{inp + out > 0 ? fmtCost(estimateCost(inp, out)) : '无数据'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}

// ---------- 记忆 ----------
export function MemoryView({ snap }: { snap: any }) {
  const gov = snap?.workspace?.governance || {}
  const fams = snap?.governance?.families || {}
  const hist = snap?.workspace?.history || {}
  const famItems = [
    { name: '适配器', value: fams.adapters?.state || '未配置' },
    { name: '记忆治理', value: fams.memory?.state || '未配置' },
    { name: '规则', value: fams.rules?.state || '未配置' },
    { name: '技能', value: fams.skills?.state || '未配置' },
  ]
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4">
        <Card><CardHeader><span>治理概览</span></CardHeader><CardContent>
          <Row k="工作流契约" v={gov.contracts || 0} /><Row k="技能数量" v={gov.skills || 0} />
          <Row k="单写者" v={gov.singleWriter ? '是' : '否'} /><Row k="任务包" v={gov.stage?.taskpack_id || '—'} />
          <Row k="模块" v={(gov.modules || []).map((m: any) => m.id).join(', ') || '—'} />
          <Row k="支持区域" v={(gov.supportAreas || []).map((a: any) => a.id).join(', ') || '—'} />
        </CardContent></Card>
        <Card><CardHeader><span>记忆治理状态</span></CardHeader><CardContent>
          {famItems.map((i) => <Row key={i.name} k={i.name} v={i.value} />)}
          <Row k="未验证能力" v={(gov.unverifiedCapabilities || []).length + ' 项'} />
        </CardContent></Card>
      </div>
      <Card>
        <CardHeader><span>错误账本</span><span className="text-[11px] text-zinc-500">共 {hist.totalErrors || 0} 条 · 防复发 {hist.repeatPreventionRequired ? '开启' : '—'}</span></CardHeader>
        <CardContent className="flex flex-col gap-2 max-h-72 overflow-auto">
          {(hist.recentErrors || []).slice(0, 10).map((e: any) => (<div key={e.errorId} className="text-[11px] py-1 border-b border-border/40 last:border-0"><span className="text-zinc-500 font-mono">{e.errorId}</span> <span className="text-zinc-300">{e.title}</span><div className="text-[10px] text-zinc-600 mt-0.5">{e.classification} · {e.status}</div></div>))}
          {(!hist.recentErrors || hist.recentErrors.length === 0) && <div className="text-xs text-zinc-500 text-center py-4">无错误记录</div>}
        </CardContent>
      </Card>
    </div>
  )
}

// ---------- 工具 ----------
export function ToolsView({ snap }: { snap: any }) {
  const areas = (snap?.executions || []).map((e: any) => e.workingArea).filter(Boolean)
  const gov = snap?.workspace?.governance || {}
  return (
    <div className="flex flex-col gap-4">
      <Card><CardHeader><span>执行工作区</span></CardHeader><CardContent className="flex flex-col gap-2">
        {areas.length ? areas.map((w: string) => (<div key={w} className="panel2 p-3 rounded text-xs font-mono text-zinc-300">{w}</div>)) : <div className="text-xs text-zinc-500 text-center py-4">暂无执行</div>}
      </CardContent></Card>
      <div className="grid grid-cols-2 gap-4">
        <Card><CardHeader><span>能力资产</span></CardHeader><CardContent>
          <Row k="工作流契约" v={gov.contracts || 0} /><Row k="技能包" v={gov.skills || 0} />
          <Row k="单写者治理" v={gov.singleWriter ? '启用' : '未启用'} />
          <Row k="任务数" v={gov.stage?.task_count || 0} />
        </CardContent></Card>
        <Card><CardHeader><span>支持区域</span></CardHeader><CardContent>
          {(gov.supportAreas || []).map((a: any) => <Row key={a.id} k={a.id} v={a.present ? '存在' : '缺失'} />)}
        </CardContent></Card>
      </div>
    </div>
  )
}

// ---------- 监控 ----------
export function MonitoringView({ services, snap }: { services: ServiceHealth[]; snap: any }) {
  const transport = snap?.transport || {}
  return (
    <div className="flex flex-col gap-4">
      <Card><CardHeader><span>服务健康</span></CardHeader><CardContent className="flex flex-col gap-2">
        {services.length ? services.map((s) => (<div key={s.name} className="flex items-center justify-between panel2 p-3 rounded"><span className="text-xs">{s.name}</span><Badge variant={s.status === 'healthy' ? 'success' : s.status === 'warning' ? 'warning' : 'error'}>{s.status === 'healthy' ? '健康' : s.status === 'warning' ? '警告' : '错误'}</Badge></div>)) : <div className="text-xs text-zinc-500 text-center py-4">暂无数据</div>}
      </CardContent></Card>
      <Card><CardHeader><span>传输与水位</span></CardHeader><CardContent>
        <Row k="传输状态" v={transport.transportState || '—'} /><Row k="事件流" v={transport.eventStreamConnected ? '已连接' : '未连接'} />
        <Row k="新鲜度" v={transport.freshnessState || '—'} /><Row k="水位" v={transport.writerWatermarkAt || '—'} />
      </CardContent></Card>
    </div>
  )
}

// ---------- 设置 ----------
export function SettingsView({ live, snap }: { live: boolean; snap: any }) {
  return (
    <div className="flex flex-col gap-4 max-w-2xl">
      <Card><CardHeader><span>数据源</span></CardHeader><CardContent>
        <Row k="Sidecar 快照 API" v={(window as any).__OBSERVER_CONFIG__?.apiBase || "动态注入"} />
        <Row k="Prometheus" v={(window as any).__OBSERVER_CONFIG__?.promBase || "动态注入"} />
        <Row k="连接状态" v={live ? '已连接' : '离线'} /><Row k="刷新间隔" v="10 秒（快照）+ 15 秒（指标）" />
      </CardContent></Card>
      <Card><CardHeader><span>版本信息</span></CardHeader><CardContent>
        <Row k="修订号" v={snap?.revision || '—'} /><Row k="Schema" v={snap?.schemaVersion || '—'} />
        <Row k="生成时间" v={snap?.generatedAt || '—'} /><Row k="数据水位" v={snap?.sourceWatermark || '—'} />
      </CardContent></Card>
      <Card><CardHeader><span>关于</span></CardHeader><CardContent className="text-xs text-zinc-400">WORK-LAB Observer · AI Agent 控制塔 · 只读投影 · 真实数据接入（sidecar + Prometheus + 本地视觉）</CardContent></Card>
    </div>
  )
}

export function DeliveryView({ snap }: { snap: any }) {
  const git = snap?.git || {}
  const ci = snap?.ci || []
  return (
    <div className="flex flex-col gap-4 overflow-auto p-4">
      <div className="grid grid-cols-2 gap-4">
        <Card><CardHeader><span>Git 状态</span></CardHeader><CardContent className="text-xs text-zinc-300">
          <div className="flex justify-between py-1"><span className="text-zinc-500">当前分支</span><span>{git.branch || 'UNKNOWN'}</span></div>
          <div className="flex justify-between py-1"><span className="text-zinc-500">HEAD</span><span className="font-mono">{git.head?.slice(0, 7) || 'UNKNOWN'}</span></div>
          <div className="flex justify-between py-1"><span className="text-zinc-500">远程一致</span><span>{git.remoteMatch === undefined ? 'UNKNOWN' : (git.remoteMatch ? '一致' : '不一致')}</span></div>
        </CardContent></Card>
        <Card><CardHeader><span>CI 状态</span></CardHeader><CardContent className="text-xs text-zinc-300">
          {ci.length ? ci.slice(0, 5).map((r: any, i: number) => (
            <div key={i} className="flex justify-between py-1"><span className="font-mono">{r.headSha?.slice(0, 7) || 'UNKNOWN'}</span><span>{r.conclusion || r.status || 'UNKNOWN'}</span></div>
          )) : <div className="text-zinc-600 py-2">无 CI 记录（UNKNOWN）</div>}
        </CardContent></Card>
      </div>
    </div>
  )
}

export function TrustView({ snap }: { snap: any }) {
  const ts = snap?.tokenSummary
  const quality = ts?.costQuality || 'UNKNOWN'
  const transport = snap?.transport || {}
  return (
    <div className="flex flex-col gap-4 overflow-auto p-4">
      <Card><CardHeader><span>数据可信度</span></CardHeader><CardContent className="text-xs text-zinc-300">
        <div className="flex justify-between py-1"><span className="text-zinc-500">成本质量</span><span>{quality}</span></div>
        <div className="flex justify-between py-1"><span className="text-zinc-500">传输状态</span><span>{transport.transportState || 'UNKNOWN'}</span></div>
        <div className="flex justify-between py-1"><span className="text-zinc-500">新鲜度</span><span>{transport.freshnessState || 'UNKNOWN'}</span></div>
        <div className="flex justify-between py-1"><span className="text-zinc-500">覆盖度</span><span>{transport.coverageNumerator != null ? (transport.coverageNumerator + '/' + (transport.coverageDenominator ?? '?') + ' · ' + (transport.coverageScope || 'UNKNOWN')) : 'UNKNOWN'}</span></div>
        <div className="flex justify-between py-1"><span className="text-zinc-500">快照生成</span><span>{snap?.generatedAt ? new Date(snap.generatedAt).toLocaleString() : 'UNKNOWN'}</span></div>
      </CardContent></Card>
      <Card><CardHeader><span>原则</span></CardHeader><CardContent className="text-xs text-zinc-500">
        未知值保持 UNKNOWN，不伪造 0；所有指标带来源/新鲜度/质量；Observer 严格只读。
      </CardContent></Card>
    </div>
  )
}
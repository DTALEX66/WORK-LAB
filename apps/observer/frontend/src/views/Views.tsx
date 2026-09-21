import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type {
  SnapshotV3, Execution, Project, ExecutionState, ProjectActivityState,
} from '@/types'
import { fmtTokens, fmtCostQuality, stateTone, activityTone } from '@/lib/api'

type Snap = SnapshotV3 | null

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  const empty = v === null || v === undefined || v === ''
  return (
    <div className="flex items-center justify-between py-1 border-b border-border/40 last:border-0">
      <span className="text-[11px] text-zinc-500">{k}</span>
      <span className="text-[11px] text-zinc-200 truncate ml-3 text-right">{empty ? 'UNKNOWN' : v}</span>
    </div>
  )
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

const STATE_TEXT: Record<string, string> = {
  RUNNING: '运行中', STARTING: '启动中', WAITING_USER: '待用户', WAITING_APPROVAL: '待审批',
  BLOCKED: '受阻', COMPLETED: '完成', FAILED: '失败', UNKNOWN: '未知',
}

// ---------- 智能体 / 项目平台 ----------
export function AgentsView({ snap }: { snap: Snap }) {
  const projects: Project[] = snap?.projects || []
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader><span>项目平台</span><span className="text-[11px] text-zinc-500">{projects.length} 个项目 · 真实 registry</span></CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {projects.length === 0 ? (
            <div className="p-8 text-center text-zinc-500 text-xs">暂无已注册项目（registry 为空）</div>
          ) : (
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-panel2 text-left text-[11px] text-zinc-500">
                  <th className="px-4 py-2 font-medium">项目</th>
                  <th className="px-3 py-2 font-medium">平台</th>
                  <th className="px-3 py-2 font-medium">活动</th>
                  <th className="px-3 py-2 font-medium">执行</th>
                  <th className="px-3 py-2 font-medium">Token</th>
                  <th className="px-3 py-2 font-medium">Git</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((p) => {
                  const tone = activityTone(p.activityState)
                  const dirty = p.git.dirtyCount
                  return (
                    <tr key={p.projectId} className="border-t border-border hover:bg-white/[0.03]">
                      <td className="px-4 py-2.5">
                        <div className="font-medium" style={{ fontSize: 12 }}>{p.displayName || p.projectId}</div>
                        <div className="text-[10px] text-zinc-600 font-mono">{p.identityState === 'RESOLVED' ? '已解析身份' : '身份未解析'}</div>
                      </td>
                      <td className="px-3 py-2.5 text-zinc-400">{p.agentPlatform || 'UNKNOWN'}</td>
                      <td className="px-3 py-2.5"><Badge variant={tone === 'active' ? 'success' : 'muted'}>{p.activityState || 'UNKNOWN'}</Badge></td>
                      <td className="px-3 py-2.5 tabular-nums text-zinc-300">{p.activeExecutionCount}</td>
                      <td className="px-3 py-2.5 tabular-nums text-zinc-300" title="costQuality（后端权威）">{fmtTokens(p.token.totalTokens)} <span className="text-[10px] text-zinc-600">{fmtCostQuality(p.token.costQuality)}</span></td>
                      <td className="px-3 py-2.5">
                        <span className="font-mono text-[11px] text-zinc-400">{p.git.branch || '—'}@{p.git.localSha ? p.git.localSha.slice(0, 7) : '—'}</span>{' '}
                        {dirty ? <Badge variant="warning">脏 {dirty}</Badge> : <Badge variant="muted">干净</Badge>}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ---------- 执行 ----------
export function ExecutionsView({ snap }: { snap: Snap }) {
  const exs: Execution[] = snap?.executions || []
  const transport = snap?.transport
  const tasks = snap?.tasks
  const taskRows = tasks ? Object.entries(tasks) : []
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader><span>执行详情</span><span className="text-[11px] text-zinc-500">{exs.length} 个执行 · 真实</span></CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {exs.length === 0 ? (
            <div className="p-8 text-center text-zinc-500 text-xs">暂无执行记录（保持 UNKNOWN）</div>
          ) : (
            <table className="w-full text-xs">
              <thead><tr className="bg-panel2 text-left text-[11px] text-zinc-500">
                <th className="px-4 py-2 font-medium">执行 ID</th>
                <th className="px-3 py-2 font-medium">Agent</th>
                <th className="px-3 py-2 font-medium">状态</th>
                <th className="px-3 py-2 font-medium">项目</th>
                <th className="px-3 py-2 font-medium">会话</th>
                <th className="px-3 py-2 font-medium">工作区</th>
              </tr></thead>
              <tbody>
                {exs.map((e) => (
                  <tr key={e.executionId} className="border-t border-border">
                    <td className="px-4 py-2 font-mono text-zinc-400">{e.executionId}</td>
                    <td className="px-3 py-2">{e.agent || 'UNKNOWN'}</td>
                    <td className="px-3 py-2"><Badge variant={toneVariant(stateTone(e.state))}>{STATE_TEXT[e.state] || e.state}</Badge></td>
                    <td className="px-3 py-2 text-zinc-300">{e.anchorProjectId || 'UNKNOWN'}</td>
                    <td className="px-3 py-2 font-mono text-[10px] text-zinc-500">{e.sessionId || 'UNKNOWN'}</td>
                    <td className="px-3 py-2 font-mono text-[10px] text-zinc-500">{e.workingArea || 'UNKNOWN'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
      <div className="grid grid-cols-2 gap-4">
        <Card><CardHeader><span>传输与水位（真实）</span></CardHeader><CardContent>
          <Row k="传输状态" v={transport?.transportState} />
          <Row k="新鲜度" v={transport?.freshnessState} />
          <Row k="事件流" v={transport?.eventStreamConnected ? '已连接' : '未连接'} />
          <Row k="最后心跳" v={transport?.lastHeartbeatAt ? new Date(transport.lastHeartbeatAt).toLocaleTimeString() : 'UNKNOWN'} />
          <Row k="写入水位" v={transport?.writerWatermarkAt ? new Date(transport.writerWatermarkAt).toLocaleTimeString() : 'UNKNOWN'} />
        </CardContent></Card>
        <Card><CardHeader><span>任务状态桶 + 快照</span></CardHeader><CardContent>
          {taskRows.length === 0
            ? <Row k="任务桶" v="UNKNOWN" />
            : taskRows.map(([k, v]) => <Row key={k} k={k} v={String(v)} />)}
          <Row k="修订号" v={snap ? String(snap.revision) : 'UNKNOWN'} />
          <Row k="数据水位" v={snap?.sourceWatermark} />
        </CardContent></Card>
      </div>
    </div>
  )
}

// ---------- 模型 / Token 用量 ----------
export function ModelsView({ snap }: { snap: Snap }) {
  const ts = snap?.tokenSummary
  const inT = ts?.inputTokens ?? null
  const outT = ts?.outputTokens ?? null
  const total = ts?.totalTokens ?? null
  const max = Math.max(inT ?? 0, outT ?? 0, 1)
  const projects: Project[] = snap?.projects || []
  const dist = [
    { name: '输入 Token', value: inT, color: 'rgb(var(--primary-rgb))' },
    { name: '输出 Token', value: outT, color: 'rgb(var(--secondary-rgb))' },
  ]
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader><span>Token 汇总</span><span className="text-[11px] text-zinc-500">质量 {fmtCostQuality(ts?.costQuality)} · 后端权威 · 前端不估算金额</span></CardHeader>
        <CardContent className="flex flex-col gap-4">
          {dist.map((d) => (
            <div key={d.name}>
              <div className="flex justify-between text-xs mb-1"><span className="flex items-center gap-1.5 text-zinc-300"><span className="w-2 h-2 rounded-full" style={{ background: d.color }} />{d.name}</span><span className="tabular-nums">{fmtTokens(d.value)}</span></div>
              <div className="h-2 rounded-full bg-zinc-700/50 overflow-hidden"><div className="h-full rounded-full" style={{ width: (max ? ((d.value ?? 0) / max) * 100 : 0) + '%', background: d.color }} /></div>
            </div>
          ))}
          <div className="flex justify-between text-xs text-zinc-400"><span>总计</span><span className="tabular-nums text-zinc-200">{fmtTokens(total)}</span></div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><span>项目 Token 明细</span></CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {projects.length === 0 ? <div className="text-xs text-zinc-500 text-center py-4">无项目</div> : (
            <table className="w-full text-xs">
              <thead><tr className="bg-panel2 text-left text-[11px] text-zinc-500"><th className="px-4 py-2 font-medium">项目</th><th className="px-3 py-2 font-medium">输入</th><th className="px-3 py-2 font-medium">输出</th><th className="px-3 py-2 font-medium">总计</th><th className="px-3 py-2 font-medium">质量</th></tr></thead>
              <tbody>
                {projects.map((p) => (
                  <tr key={p.projectId} className="border-t border-border">
                    <td className="px-4 py-2">{p.displayName || p.projectId}</td>
                    <td className="px-3 py-2 tabular-nums text-zinc-300">{fmtTokens(p.token.inputTokens)}</td>
                    <td className="px-3 py-2 tabular-nums text-zinc-300">{fmtTokens(p.token.outputTokens)}</td>
                    <td className="px-3 py-2 tabular-nums">{fmtTokens(p.token.totalTokens)}</td>
                    <td className="px-3 py-2 tabular-nums text-zinc-400">{fmtCostQuality(p.token.costQuality)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ---------- 记忆 / 治理 ----------
export function MemoryView({ snap }: { snap: Snap }) {
  const gov = snap?.governance
  const fams = gov?.families
  const hist = (snap?.workspace as any)?.history || {}
  const famItems = [
    { name: '规则', state: fams?.rules?.state, drift: fams?.rules?.drift },
    { name: '技能', state: fams?.skills?.state, drift: fams?.skills?.drift },
    { name: '记忆', state: fams?.memory?.state, drift: fams?.memory?.drift },
    { name: '适配器', state: fams?.adapters?.state, drift: fams?.adapters?.drift },
  ]
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4">
        <Card><CardHeader><span>治理漂移状态（真实）</span></CardHeader><CardContent>
          {famItems.map((i) => (
            <Row key={i.name} k={i.name} v={<span>{i.state || 'UNKNOWN'}{i.drift ? ' · 漂移 ' + i.drift : ''}</span>} />
          ))}
        </CardContent></Card>
        <Card><CardHeader><span>错误账本（workspace.history）</span></CardHeader><CardContent>
          <Row k="总错误数" v={(hist.totalErrors != null ? String(hist.totalErrors) : 'UNKNOWN')} />
          {(hist.recentErrors || []).slice(0, 6).map((e: any, i: number) => (
            <div key={i} className="text-[11px] py-1 border-b border-border/40 last:border-0">
              <span className="text-zinc-500 font-mono">{e.errorId || 'UNKNOWN'}</span>{' '}
              <span className="text-zinc-300">{e.title || e.classification || ''}</span>
            </div>
          ))}
          {(!hist.recentErrors || hist.recentErrors.length === 0) && <div className="text-xs text-zinc-500 text-center py-4">无错误记录（UNKNOWN）</div>}
        </CardContent></Card>
      </div>
    </div>
  )
}

// ---------- 工具 / 能力 ----------
export function ToolsView({ snap }: { snap: Snap }) {
  const areas = Array.from(new Set((snap?.executions || []).map((e) => e.workingArea).filter((a): a is string => !!a)))
  const gov = snap?.governance
  return (
    <div className="flex flex-col gap-4">
      <Card><CardHeader><span>执行工作区</span></CardHeader><CardContent className="flex flex-col gap-2">
        {areas.length ? areas.map((w) => <div key={w} className="panel2 p-3 rounded text-xs font-mono text-zinc-300">{w}</div>) : <div className="text-xs text-zinc-500 text-center py-4">暂无执行工作区（UNKNOWN）</div>}
      </CardContent></Card>
      <Card><CardHeader><span>治理家族状态</span></CardHeader><CardContent>
        {(['rules', 'skills', 'memory', 'adapters'] as const).map((k) => (
          <Row key={k} k={k} v={gov?.families?.[k]?.state || 'UNKNOWN'} />
        ))}
      </CardContent></Card>
    </div>
  )
}

// ---------- 监控 / 系统 ----------
export function MonitoringView({ snap }: { snap: Snap }) {
  const transport = snap?.transport
  const cov = snap?.coverage
  return (
    <div className="flex flex-col gap-4">
      <Card><CardHeader><span>传输真值（永不伪造 LIVE）</span></CardHeader><CardContent>
        <Row k="传输状态" v={<Badge variant={transport?.transportState === 'LIVE' ? 'success' : transport?.transportState === 'OFFLINE' ? 'error' : 'muted'}>{transport?.transportState || 'UNKNOWN'}</Badge>} />
        <Row k="新鲜度" v={transport?.freshnessState || 'UNKNOWN'} />
        <Row k="连接起点" v={transport?.connectedSince ? new Date(transport.connectedSince).toLocaleTimeString() : 'UNKNOWN'} />
        <Row k="覆盖度" v={cov && cov.numerator != null ? cov.numerator + '/' + (cov.denominator ?? '?') + ' · ' + (cov.scope || 'UNKNOWN') : 'UNKNOWN'} />
      </CardContent></Card>
      <Card><CardHeader><span>说明</span></CardHeader><CardContent className="text-xs text-zinc-500">
        服务健康 = 传输真值，不是伪造的 healthy。LIVE 仅当 live-gate verdict 为 LIVE；canonical readback 失败回退 DELAYED/OFFLINE。Observer 严格只读。
      </CardContent></Card>
    </div>
  )
}

// ---------- 交付 ----------
export function DeliveryView({ snap }: { snap: Snap }) {
  const git = snap?.git
  const ci = snap?.ci || []
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4">
        <Card><CardHeader><span>Git 状态（真实）</span></CardHeader><CardContent>
          <Row k="本地" v={git?.localSha ? git.localSha.slice(0, 7) : 'UNKNOWN'} />
          <Row k="远程" v={git?.remoteSha ? git.remoteSha.slice(0, 7) : 'UNKNOWN'} />
          <Row k="CI HEAD" v={git?.ciSha ? git.ciSha.slice(0, 7) : 'UNKNOWN'} />
          <Row k="匹配状态" v={<Badge variant={git?.matchState === 'MATCH' ? 'success' : git?.matchState === 'DRIFT' ? 'error' : 'muted'}>{git?.matchState || 'UNKNOWN'}</Badge>} />
        </CardContent></Card>
        <Card><CardHeader><span>CI 运行</span></CardHeader><CardContent>
          {ci.length ? ci.slice(0, 5).map((r, i) => (
            <div key={i} className="flex justify-between py-1 text-xs">
              <span className="font-mono text-zinc-400">{r.headSha ? r.headSha.slice(0, 7) : 'UNKNOWN'} · {r.workflow || 'UNKNOWN'}</span>
              <Badge variant={r.conclusion === 'success' || r.status === 'success' ? 'success' : r.status ? 'warning' : 'muted'}>{r.conclusion || r.status || 'UNKNOWN'}</Badge>
            </div>
          )) : <div className="text-zinc-600 py-2 text-xs">无 CI 记录（UNKNOWN）</div>}
        </CardContent></Card>
      </div>
    </div>
  )
}

// ---------- 可信 ----------
export function TrustView({ snap }: { snap: Snap }) {
  const ts = snap?.tokenSummary
  const quality = ts?.costQuality || 'UNKNOWN'
  const transport = snap?.transport
  const cov = snap?.coverage
  const refs = snap?.sourceRefs || []
  return (
    <div className="flex flex-col gap-4">
      <Card><CardHeader><span>数据可信度（真实投影）</span></CardHeader><CardContent>
        <Row k="Token 质量" v={<Badge variant={quality === 'EXACT' ? 'success' : quality === 'ESTIMATED' ? 'warning' : 'muted'}>{quality}</Badge>} />
        <Row k="传输状态" v={transport?.transportState || 'UNKNOWN'} />
        <Row k="新鲜度" v={transport?.freshnessState || 'UNKNOWN'} />
        <Row k="覆盖度" v={cov && cov.numerator != null ? cov.numerator + '/' + (cov.denominator ?? '?') + ' · ' + (cov.scope || 'UNKNOWN') : 'UNKNOWN'} />
        <Row k="证据引用数" v={refs.length ? String(refs.length) : '0'} />
        <Row k="快照生成" v={snap?.generatedAt ? new Date(snap.generatedAt).toLocaleString() : 'UNKNOWN'} />
      </CardContent></Card>
      <Card><CardHeader><span>原则</span></CardHeader><CardContent className="text-xs text-zinc-500">
        未知值保持 UNKNOWN，不伪造 0；Token/成本仅后端投影的质量标签（EXACT/ESTIMATED/UNKNOWN），前端不算金额、不算汇率、不算配额；Observer 严格只读，不构成第二 Update Authority。
      </CardContent></Card>
    </div>
  )
}

// ---------- 设置 ----------
export function SettingsView({ snap }: { snap: Snap }) {
  const cfg = (window as any).__OBSERVER_CONFIG__
  const descriptorSource = cfg?.apiBase ? 'window-config' : 'static-preview/tauri-injected'
  return (
    <div className="flex flex-col gap-4 max-w-2xl">
      <Card><CardHeader><span>数据源（真实）</span></CardHeader><CardContent>
        <Row k="快照端点来源" v={descriptorSource} />
        <Row k="事件流" v={snap?.transport.eventsUrl || 'UNKNOWN'} />
        <Row k="传输状态" v={snap?.transport.transportState || 'UNKNOWN'} />
      </CardContent></Card>
      <Card><CardHeader><span>版本信息</span></CardHeader><CardContent>
        <Row k="修订号" v={snap ? String(snap.revision) : 'UNKNOWN'} />
        <Row k="Schema" v={snap?.schemaVersion || 'UNKNOWN'} />
        <Row k="生成时间" v={snap?.generatedAt ? new Date(snap.generatedAt).toLocaleString() : 'UNKNOWN'} />
        <Row k="数据水位" v={snap?.sourceWatermark || 'UNKNOWN'} />
      </CardContent></Card>
      <Card><CardHeader><span>关于</span></CardHeader><CardContent className="text-xs text-zinc-400">
        WORK-LAB Observer · 客户端中立控制塔 · 只读投影 · 严格真实（sidecar v3 snapshot + SSE；无 Prometheus/本地资源伪造）
      </CardContent></Card>
    </div>
  )
}

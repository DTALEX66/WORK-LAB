// WORK-LAB Observer — real data source (sidecar snapshot API)
import type { Agent, ServiceHealth, TimelineEvent, CostPoint } from '@/types'

const SNAPSHOT_URL = 'http://127.0.0.1:61867/api/v1/snapshot'

export interface LiveSnapshot {
  generatedAt: string
  projects: any[]
  executions: any[]
  tokenSummary: { inputTokens: number; outputTokens: number; totalTokens: number }
  tasks: any[]
  revision?: string
  workspace?: any
  governance?: any
  transport?: any
  sourceWatermark?: string
}

export async function fetchSnapshot(): Promise<LiveSnapshot | null> {
  try {
    const res = await fetch(SNAPSHOT_URL, { headers: { Origin: 'http://127.0.0.1:8090' } })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

// DeepSeek reference rates ($/M tokens) for ESTIMATED cost
const RATE_INPUT = 0.5
const RATE_OUTPUT = 2.0

export function estimateCost(input: number, output: number): number {
  return (input / 1e6) * RATE_INPUT + (output / 1e6) * RATE_OUTPUT
}

export function fmtTokens(n: number | null): string {
  // WLR-130: unknown stays UNKNOWN, never 0
  if (n == null) return 'UNKNOWN'
  return n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : (n / 1e3).toFixed(0) + 'k'
}

// USD -> CNY reference rate for cost display (rate itself is a reference, kept here)
const CNY_RATE = 7.2

export function fmtCost(usd: number | null): string {
  if (usd == null) return 'UNKNOWN'
  return '¥' + (usd * CNY_RATE).toFixed(2)
}

// Map live executions -> Agent rows (keep the same Agent contract)
export function executionsToAgents(snap: LiveSnapshot): Agent[] {
  if (!snap || !snap.executions) return []
  return snap.executions.map((ex: any, i: number) => {
    const proj = (snap.projects || []).find((p: any) => p.projectId === ex.anchorProjectId)
    // WLR-130: truth-first — unknown stays unknown (null), never fabricated 0.
    const tok = proj?.token
    const state = String(ex.state || 'UNKNOWN').toLowerCase()
    const status: Agent['status'] = state.includes('run') ? 'running' : state.includes('fail') ? 'failed' : state.includes('pend') ? 'pending' : 'idle'
    const total = tok?.totalTokens ?? null
    const cost = (tok?.inputTokens == null || tok?.outputTokens == null) ? null : estimateCost(tok.inputTokens, tok.outputTokens)
    return {
      id: ex.executionId || ('exec-' + i),
      name: ex.agent || 'agent',
      status,
      runtime: proj?.agentPlatform || '—',
      task: ex.anchorProjectId || '—',
      model: '—',
      tokens: total,
      cost,
      durationSec: 0,
      usagePct: total == null ? null : Math.min(100, Math.round(total / 3e7 * 100)),
      trend: [],
    }
  })
}

export function snapshotToServices(snap: LiveSnapshot | null): ServiceHealth[] {
  if (!snap) return []
  const items: ServiceHealth[] = []
  for (const p of snap.projects || []) {
    items.push({
      name: p.displayName || p.projectId || 'project',
      status: p.activityState === 'ACTIVE' ? 'healthy' : p.activityState === 'DEGRADED' ? 'warning' : 'error',
      usage: (p.activeExecutionCount || 0) + ' exec',
    })
  }
  items.push({ name: 'Sidecar', status: 'healthy', usage: 'snapshot api' })
  return items.slice(0, 8)
}

export function snapshotToTimeline(snap: LiveSnapshot | null): TimelineEvent[] {
  if (!snap) return []
  return (snap.executions || []).map((ex: any, i: number) => {
    const state = String(ex.state || '').toLowerCase()
    const type: TimelineEvent['type'] = state.includes('fail') ? 'failed' : state.includes('pend') ? 'approval' : state.includes('run') ? 'running' : 'success'
    const time = new Date(snap.generatedAt).toTimeString().slice(0, 5)
    return { time, type, label: ex.agent + ' · ' + (ex.anchorProjectId || '') }
  }).concat([
    { time: new Date(snap.generatedAt).toTimeString().slice(0, 5), type: 'success' as const, label: 'Snapshot ' + String(snap.revision || '').slice(0, 7) },
  ])
}

export function snapshotToCosts(snap: LiveSnapshot | null): CostPoint[] {
  if (!snap) return []
  return (snap.projects || []).map((p: any, i: number) => {
    const t = p.token || {}
    // WLR-130: missing usage -> null cost (never fabricated 0)
    const input = t.inputTokens == null ? null : Number(t.inputTokens)
    const output = t.outputTokens == null ? null : Number(t.outputTokens)
    const cost = (input == null || output == null) ? null : estimateCost(input, output)
    return { date: p.displayName || p.projectId || String(i), cost }
  })
}
// --- Prometheus real time-series (KPI trends, cost line, resources) ---
const PROM_URL = 'http://127.0.0.1:9090'

export async function promQuery(query: string): Promise<number | null> {
  try {
    const res = await fetch(PROM_URL + '/api/v1/query?query=' + encodeURIComponent(query))
    if (!res.ok) return null
    const j = await res.json()
    const v = j?.data?.result?.[0]?.value?.[1]
    return v === undefined ? null : Number(v)
  } catch { return null }
}

export async function promRange(query: string, minutes: number = 360): Promise<number[]> {
  const end = Math.floor(Date.now() / 1000)
  const start = end - minutes * 60
  const step = Math.max(60, Math.floor(minutes * 60 / 40))
  try {
    const url = PROM_URL + '/api/v1/query_range?query=' + encodeURIComponent(query) + '&start=' + start + '&end=' + end + '&step=' + step
    const res = await fetch(url)
    if (!res.ok) return []
    const j = await res.json()
    const rows = j?.data?.result?.[0]?.values || []
    return rows.map((r: any[]) => Number(r[1])).filter((n: number) => Number.isFinite(n))
  } catch { return [] }
}

export interface SysResources { cpu: number; mem: number; disk: number; netSent: number; netRecv: number }

export async function fetchResources(): Promise<SysResources | null> {
  const [cpu, mem, disk, netSent, netRecv] = await Promise.all([
    promQuery('wlobs_sys_cpu_percent'),
    promQuery('wlobs_sys_memory_percent'),
    promQuery('wlobs_sys_disk_percent'),
    promQuery('wlobs_sys_net_bytes{direction="sent"}'),
    promQuery('wlobs_sys_net_bytes{direction="recv"}'),
  ])
  if (cpu === null) return null
  return { cpu, mem: mem || 0, disk: disk || 0, netSent: netSent || 0, netRecv: netRecv || 0 }
}

import type { Agent, ServiceHealth, TimelineEvent, ResourceMetric, CostPoint } from '@/types'

const RUNTIMES = ['DSH', 'Hermes', 'Codex', 'Open Design', 'Local LLM', 'MCP']
const MODELS = ['deepseek-v4', 'claude-4.5', 'gpt-5', 'qwen3', 'llama-4', 'gpt-o3']
const TASKS = ['代码审查', '设计迭代', '测试执行', '文档生成', '数据标注', '知识检索', 'API 集成', '报告生成']

function pick<T>(arr: T[]): T { return arr[Math.floor(Math.random() * arr.length)] }

export function generateAgents(count: number): Agent[] {
  const statuses: Agent['status'][] = ['running', 'running', 'pending', 'idle', 'failed']
  return Array.from({ length: count }, (_, i) => {
    const base = Math.floor(Math.random() * 60) + 10
    return {
      id: `ag-${String(i + 1).padStart(3, '0')}`,
      name: `agent-${String.fromCharCode(97 + (i % 26))}${Math.floor(i / 26) + 1}`,
      status: statuses[Math.floor(Math.random() * statuses.length)],
      runtime: pick(RUNTIMES),
      task: pick(TASKS),
      model: pick(MODELS),
      tokens: Math.floor(Math.random() * 900000) + 50000,
      cost: Math.round((Math.random() * 4 + 0.1) * 100) / 100,
      durationSec: Math.floor(Math.random() * 3600) + 30,
      usagePct: Math.floor(Math.random() * 100),
      trend: Array.from({ length: 8 }, (_, j) => base + Math.floor(Math.sin(j / 1.6) * 20 + Math.random() * 10)),
    }
  })
}

export const mockServices: ServiceHealth[] = [
  { name: 'API Gateway', status: 'healthy', usage: '1.2k req/s' },
  { name: 'Auth Service', status: 'healthy', usage: '240 ops/s' },
  { name: 'Agent Scheduler', status: 'healthy', usage: '36 active' },
  { name: 'Task Queue', status: 'healthy', usage: '128 queued' },
  { name: 'Vector DB', status: 'warning', usage: '78% load' },
  { name: 'Memory Store', status: 'healthy', usage: '42% used' },
  { name: 'Model Router', status: 'healthy', usage: '8 models' },
  { name: 'Storage', status: 'healthy', usage: '61% used' },
]

export const mockTimeline: TimelineEvent[] = [
  { time: '14:02', type: 'running', label: 'Agent Start · ag-014' },
  { time: '14:05', type: 'success', label: 'Tool Call · git' },
  { time: '14:09', type: 'running', label: 'Model Response · deepseek-v4' },
  { time: '14:12', type: 'approval', label: 'Human Approval · 需确认' },
  { time: '14:16', type: 'success', label: 'Completed · ag-008' },
  { time: '14:21', type: 'failed', label: 'Failed · ag-031' },
  { time: '14:25', type: 'running', label: 'Tool Call · mcp-fs' },
]

export const mockResources: ResourceMetric[] = [
  { label: 'CPU', value: 32 },
  { label: 'Memory', value: 64 },
  { label: 'GPU', value: 48 },
  { label: 'Network', value: 23 },
]

export const mockCosts: CostPoint[] = [
  { date: '05-11', cost: 218 }, { date: '05-12', cost: 284 }, { date: '05-13', cost: 197 },
  { date: '05-14', cost: 342 }, { date: '05-15', cost: 265 }, { date: '05-16', cost: 310 },
  { date: '05-17', cost: 298 },
]

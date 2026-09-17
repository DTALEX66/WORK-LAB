export type AgentStatus = 'running' | 'pending' | 'failed' | 'idle'

export interface Agent {
  id: string
  name: string
  status: AgentStatus
  runtime: string
  task: string
  model: string
  // WLR-130: unknown stays null (truth-first), never fabricated 0
  tokens: number | null
  cost: number | null
  durationSec: number
  usagePct: number | null
  trend: number[]
}

export interface ServiceHealth {
  name: string
  status: 'healthy' | 'warning' | 'error'
  usage: string
}

export interface TimelineEvent {
  time: string
  type: 'success' | 'running' | 'approval' | 'failed'
  label: string
}

export interface ResourceMetric {
  label: string
  value: number
}

export interface CostPoint {
  date: string
  cost: number | null  // WLR-130: unknown stays null
}

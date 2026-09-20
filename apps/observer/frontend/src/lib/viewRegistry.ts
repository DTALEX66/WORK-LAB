// U04: typed frontend view registry. One source of truth for the navigation
// lanes. Replaces the array-index coupling in App.tsx (views[view]) where the
// Sidebar had 8 items but the views array had 10, making Delivery/Trust/
// Settings unreachable. Every view is now reachable by a stable id.
//
// Icons come from lucide-react; the component is a lazy-free static reference
// (all views are small and already bundled). Adding a view = add one row here.
import type { ComponentType } from 'react'
import type { LucideIcon } from 'lucide-react'
import {
  LayoutDashboard, Bot, PlayCircle, Cpu, Brain, Wrench, Activity,
  Package, ShieldCheck, Settings,
} from 'lucide-react'
import {
  AgentsView, ExecutionsView, ModelsView, MemoryView, ToolsView,
  MonitoringView, DeliveryView, TrustView, SettingsView,
} from '@/views/Views'
import { SoftwareView } from '@/views/SoftwareView'

export interface ViewEntry {
  id: string
  label: string
  icon: LucideIcon
  component: ComponentType<any>
  /** taskpack lane the view satisfies */
  lane: 'overview' | 'agents' | 'executions' | 'models' | 'memory' | 'tools' | 'monitoring' | 'delivery' | 'trust' | 'settings' | 'software'
}

// TaskPack U04 lanes: Overview, Projects, Agents, Executions, Models/Usage,
// Memory, Tools/Capabilities, Monitoring/System, Delivery, Trust, Settings.
// Projects is folded into the Agents/Projects panel (AgentsView already renders
// the per-project platform cards) — documented decision, not a separate view.
export const VIEW_REGISTRY: ViewEntry[] = [
  { id: 'agents',       label: '智能体', icon: Bot,             component: AgentsView,       lane: 'agents' },
  { id: 'executions',   label: '执行',   icon: PlayCircle,      component: ExecutionsView,   lane: 'executions' },
  { id: 'models',       label: '模型',   icon: Cpu,             component: ModelsView,       lane: 'models' },
  { id: 'memory',       label: '记忆',   icon: Brain,           component: MemoryView,       lane: 'memory' },
  { id: 'tools',        label: '工具',   icon: Wrench,          component: ToolsView,        lane: 'tools' },
  { id: 'monitoring',   label: '监控',   icon: Activity,        component: MonitoringView,   lane: 'monitoring' },
  { id: 'delivery',     label: '交付',   icon: Package,         component: DeliveryView,     lane: 'delivery' },
  { id: 'trust',        label: '可信',   icon: ShieldCheck,     component: TrustView,        lane: 'trust' },
  // S31/32: read-only software location panel (location drift / duplicate install
  // surfaced instead of a false "Healthy").
  { id: 'software',     label: '软件',   icon: LayoutDashboard, component: SoftwareView,     lane: 'software' },
  { id: 'settings',     label: '设置',   icon: Settings,        component: SettingsView,   lane: 'settings' },
]

export const VIEW_BY_ID: Record<string, ViewEntry> = Object.fromEntries(
  VIEW_REGISTRY.map((v) => [v.id, v])
)

// Overview is rendered inline in App.tsx (KPI cards + agents + cost) and is the
// default landing view, so it is not a registry entry with its own component —
// it is a synthetic first lane.
export const OVERVIEW_ID = 'overview'

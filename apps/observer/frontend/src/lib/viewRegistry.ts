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
  Package, FolderGit2, ShieldCheck, Settings,
  ScrollText, History, CheckCircle2, Plug, PackageCheck, SquareKanban,
  Workflow, Network, GitBranch, FileSearch,
} from 'lucide-react'
import {
  AgentsView, ExecutionsView, ModelsView, MemoryView, ToolsView,
  MonitoringView, DeliveryView, TrustView, SettingsView, ProjectsView,
} from '@/views/Views'
import { SoftwareView } from '@/views/SoftwareView'
// D3 (2026-09-26 stage D): primary Work lane — the first read-only visible
// closed loop (entry -> project -> task/execution -> state/failure ->
// Context/Evidence -> next step) with a right-side Inspector.
import { WorkView } from '@/views/WorkView'
// REQ-RANGE-20261007: the evidence slice lane — three columns per artifact (identity / slice / verdict),
// reading the sidecar's typed `worklab/evidence-range-result/v1` body instead of an opaque reference.
import { EvidenceView } from '@/views/EvidenceView'
// UI_VIEWS (20260921): five L7-aligned governance lanes (honest projections).
import { RulesPolicyView } from '@/views/RulesPolicyView'
import { AuditTrailView } from '@/views/AuditTrailView'
import { ApprovalsView } from '@/views/ApprovalsView'
import { IntegrationsView } from '@/views/IntegrationsView'
import { TaskPacksView } from '@/views/TaskPacksView'
// L10 (2026-09-27): B10 final-deployable lanes (B07 IA page matrix) —
// Workflows / Workflow Editor / Observer / Execution Detail.
import { WorkflowsView } from '@/views/WorkflowsView'
import { WorkflowEditorView } from '@/views/WorkflowEditorView'
import { ObserverView } from '@/views/ObserverView'
import { ExecutionDetailView } from '@/views/ExecutionDetailView'

export interface ViewEntry {
  id: string
  label: string
  icon: LucideIcon
  component: ComponentType<any>
  /** taskpack lane the view satisfies */
  lane:
    | 'overview' | 'agents' | 'executions' | 'models' | 'memory' | 'tools'
    | 'monitoring' | 'delivery' | 'trust' | 'settings' | 'software'
    | 'projects'
    // D3 (2026-09-26 stage D): primary Work lane
    | 'work'
    // UI_VIEWS (20260921): L7 governance lanes
    | 'rules-policy' | 'audit' | 'approvals' | 'integrations' | 'task-packs'
    // L10 (2026-09-27): B10 final-deployable lanes
    // L10 (2026-09-27): B10 final-deployable lanes
    | 'workflows' | 'workflow-editor' | 'observer' | 'execution-detail'
    // REQ-RANGE-20261007: evidence slice lane (identity / slice / verdict)
    | 'evidence'
}

// TaskPack U04 lanes: Overview, Projects, Agents, Executions, Models/Usage,
// Memory, Tools/Capabilities, Monitoring/System, Delivery, Trust, Settings.
// Projects is folded into the Agents/Projects panel (AgentsView already renders
// the per-project platform cards) — documented decision, not a separate view.
export const VIEW_REGISTRY: ViewEntry[] = [
  // D3 (2026-09-26 stage D): Work is the primary read-only closed-loop lane
  // (entry -> project -> task/execution -> state/failure -> Context/Evidence
  // -> next step) with a right-side Inspector. It reuses the SAME real v3
  // snapshot projection (no second ledger, no fabricated fields).
  { id: 'work',         label: '工作',   icon: SquareKanban,  component: WorkView,         lane: 'work' },
  { id: 'agents',       label: '智能体', icon: Bot,             component: AgentsView,       lane: 'agents' },
  // P1-D §3.1 (2026-09-26): Projects promoted to a first-level entry. The
  // project-platform table was folded into AgentsView (U04); it is now a
  // dedicated read-only view reusing the SAME real snap.projects projection.
  { id: 'projects',     label: '项目',   icon: FolderGit2,     component: ProjectsView,     lane: 'projects' },
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
  // UI_VIEWS (20260921): L7-aligned governance lanes (honest projections,
  // read-only; each view renders an EmptyState/UnknownState when its data
  // source is absent from the snapshot).
  { id: 'rules-policy', label: '规则策略', icon: ScrollText,    component: RulesPolicyView, lane: 'rules-policy' },
  { id: 'audit',        label: '审计追踪', icon: History,       component: AuditTrailView,  lane: 'audit' },
  { id: 'approvals',    label: '审批中心', icon: CheckCircle2,  component: ApprovalsView,   lane: 'approvals' },
  { id: 'integrations', label: '集成/MCP', icon: Plug,          component: IntegrationsView, lane: 'integrations' },
  { id: 'task-packs',   label: '任务包',   icon: PackageCheck,  component: TaskPacksView,   lane: 'task-packs' },
  // L10 (2026-09-27): B10 final-deployable lanes (B07 page matrix) —
  // Workflows / interactive Workflow Editor / read-only Observer /
  // Execution Detail.
  { id: 'workflows',         label: '工作流',   icon: Workflow,    component: WorkflowsView,         lane: 'workflows' },
  { id: 'workflow-editor',   label: '编辑器',   icon: GitBranch,   component: WorkflowEditorView,    lane: 'workflow-editor' },
  { id: 'observer',         label: '观察者',   icon: Network,     component: ObserverView,          lane: 'observer' },
  { id: 'execution-detail',  label: '执行详情', icon: PlayCircle,  component: ExecutionDetailView,   lane: 'execution-detail' },
  // REQ-RANGE-20261007: the evidence lane rides the same registry so the per-lane truth sweeps cover it
  // the moment it exists — a lane that only its own test file can reach is the lane that regresses.
  { id: 'evidence',          label: '证据区间', icon: FileSearch,  component: EvidenceView,          lane: 'evidence' },
]

export const VIEW_BY_ID: Record<string, ViewEntry> = Object.fromEntries(
  VIEW_REGISTRY.map((v) => [v.id, v])
)

// Overview is rendered inline in App.tsx (KPI cards + agents + cost) and is the
// default landing view, so it is not a registry entry with its own component —
// it is a synthetic first lane.
export const OVERVIEW_ID = 'overview'

// N-1: the label lived in App.tsx, Sidebar.tsx and OverviewView.tsx as three
// separate string literals, so the nav could say 总览 while the page header said
// anything else. Overview has no registry entry, so it needs its own constant.
export const OVERVIEW_LABEL = '总览'

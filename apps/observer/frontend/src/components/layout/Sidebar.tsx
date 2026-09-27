import * as React from 'react'
import { LayoutDashboard, ChevronsLeft, ChevronsRight, ChevronDown, ChevronRight } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { VIEW_REGISTRY, OVERVIEW_ID } from '@/lib/viewRegistry'

/**
 * UI_SHELL (20260921): grouped, collapsible navigation rail.
 *  - Desktop: 260px expanded ↔ 72px collapsed (icon-only + tooltip), toggled
 *    by the parent (App). Colors resolve through SPEC-A CSS variables so both
 *    Dark/Light themes invert correctly.
 *  - Groups (P1-D §3.1 seven primary entries: Home/Work/Agents/Projects/
 *    Governance/Integrations/System, see NAV_GROUPS) are foldable when
 *    expanded; all registry lanes stay reachable by a stable id.
 *  - Mobile (<768px): rendered as a fixed overlay drawer with a backdrop,
 *    open/close driven by the parent. No new dependencies — plain media query
 *    (Tailwind `md:` = 768px) + conditional render.
 *
 * Lanes come from VIEW_REGISTRY (SPEC-C added the five governance lanes), so
 * every view stays reachable by a stable id — the original U04 goal.
 */
interface LaneDef {
  id: string
  label: string
  icon: LucideIcon
}

// L10 (2026-09-27): B07 IA page matrix regrouping — 7 primary nav groups
// covering all 22 reachable lanes exactly once (the P1-01 invariant, now
// including the four B10 lanes: workflows / workflow-editor / observer /
// execution-detail). D3 `work` lane still leads the work group.
export const NAV_GROUPS: { key: string; label: string; ids: string[] }[] = [
  { key: 'home',   label: '首页',   ids: [OVERVIEW_ID] },
  { key: 'work',   label: '工作',   ids: ['work', 'executions', 'task-packs', 'delivery', 'execution-detail'] },
  { key: 'agents', label: '智能体', ids: ['agents'] },
  { key: 'projects', label: '项目', ids: ['projects'] },
  { key: 'gov',    label: '治理',   ids: ['workflows', 'rules-policy', 'approvals', 'audit', 'trust'] },
  { key: 'integrations', label: '集成', ids: ['integrations', 'workflow-editor'] },
  { key: 'system', label: '系统',   ids: ['observer', 'software', 'models', 'monitoring', 'memory', 'tools', 'settings'] },
]

function buildLanes(): Map<string, LaneDef> {
  const overview: LaneDef = { id: OVERVIEW_ID, label: '总览', icon: LayoutDashboard }
  const map = new Map<string, LaneDef>([[OVERVIEW_ID, overview]])
  for (const e of VIEW_REGISTRY) {
    if (e.component) map.set(e.id, { id: e.id, label: e.label, icon: e.icon })
  }
  return map
}

export interface SidebarProps {
  activeView: string
  onSelect: (id: string) => void
  /** desktop rail collapsed (icons only) */
  collapsed?: boolean
  onToggleCollapse?: () => void
  /** mobile overlay open */
  mobileOpen?: boolean
  onCloseMobile?: () => void
}

export function Sidebar({
  activeView,
  onSelect,
  collapsed = false,
  onToggleCollapse,
  mobileOpen = false,
  onCloseMobile,
}: SidebarProps) {
  const lanes = React.useMemo(buildLanes, [])
  const [openGroups, setOpenGroups] = React.useState<Set<string>>(
    () => new Set(NAV_GROUPS.map((g) => g.key)),
  )

  const toggleGroup = (key: string) => {
    setOpenGroups((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const Header = ({ isCollapsed }: { isCollapsed: boolean }) => (
    <div className={cn('flex items-center gap-3 px-3 py-4', isCollapsed && 'justify-center px-0')}>
      {/* L10: B10 `.brand-mark` — 48px gradient rounded tile + "WL" 900 glyph,
          primary glow shadow (D-02: B10 brand lock wins over L7). */}
      <div
        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-sm font-black tracking-wide text-white"
        style={{
          background: [
            'radial-gradient(circle at 30% 30%, color-mix(in srgb, rgb(var(--primary-rgb)) 80%, white 6%), transparent 45%)',
            'linear-gradient(135deg, color-mix(in srgb, rgb(var(--primary-rgb)) 80%, white 3%), color-mix(in srgb, rgb(var(--secondary-rgb)) 55%, rgb(var(--primary-rgb))))',
          ].join(', '),
          boxShadow: '0 0 0 1px color-mix(in srgb, rgb(var(--primary-rgb)) 25%, white 5%), 0 10px 30px var(--glow-primary)',
        }}
        aria-hidden="true"
      >
        WL
      </div>
      {!isCollapsed && (
        <div className="min-w-0">
          <div className="text-[15px] font-semibold text-ink leading-tight">WORK-LAB</div>
          <div className="mt-0.5 text-[10px] uppercase tracking-[0.12em] text-primary">AI Workflow Control Plane</div>
        </div>
      )}
      {onToggleCollapse && (
        <button
          type="button"
          onClick={onToggleCollapse}
          title={isCollapsed ? '展开' : '折叠'}
          aria-label={isCollapsed ? '展开导航' : '折叠导航'}
          className={cn(
            'hidden md:inline-flex h-7 w-7 items-center justify-center rounded-md text-muted transition-colors duration-fast',
            'hover:bg-panel2 hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
            !isCollapsed && 'ml-auto',
          )}
        >
          {isCollapsed ? <ChevronsRight size={16} /> : <ChevronsLeft size={16} />}
        </button>
      )}
    </div>
  )

  // Icon-only rail (desktop collapsed OR used as the compact list)
  const RailItems = () => (
    <div className="flex flex-col items-center gap-1 px-2">
      {[...lanes.values()].map((l) => {
        const Icon = l.icon
        const active = activeView === l.id
        return (
          <button
            key={l.id}
            type="button"
            onClick={() => onSelect(l.id)}
            title={l.label}
            aria-label={l.label}
            className={cn(
              'h-10 w-10 rounded-md flex items-center justify-center transition-colors duration-fast',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
              active ? 'bg-primary/15 text-primary' : 'text-muted hover:bg-panel2 hover:text-ink',
            )}
          >
            <Icon size={18} />
          </button>
        )
      })}
    </div>
  )

  // Grouped nav (expanded desktop + mobile)
  const GroupedNav = () => (
    <nav className="flex-1 overflow-y-auto px-2 py-1" aria-label="主导航">
      {NAV_GROUPS.map((g) => {
        const items = g.ids.map((id) => lanes.get(id)).filter(Boolean) as LaneDef[]
        if (items.length === 0) return null
        const open = openGroups.has(g.key)
        return (
          <div key={g.key} className="mb-1">
            <button
              type="button"
              onClick={() => toggleGroup(g.key)}
              aria-expanded={open}
              className={cn(
                'flex w-full items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-muted transition-colors duration-fast',
                'hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
              )}
            >
              {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
              <span className="truncate">{g.label}</span>
            </button>
            {open && (
              <div className="mt-0.5 flex flex-col gap-0.5">
                {items.map((l) => {
                  const Icon = l.icon
                  const active = activeView === l.id
                  return (
                    <button
                      key={l.id}
                      type="button"
                      onClick={() => onSelect(l.id)}
                      title={l.label}
                      aria-current={active ? 'page' : undefined}
                      className={cn(
                        'group relative flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm transition-all duration-fast',
                        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
                        active
                          ? 'text-ink'
                          : 'text-muted hover:bg-panel2/78 hover:text-ink hover:translate-x-[3px]',
                      )}
                      style={active ? {
                        background: [
                          'linear-gradient(180deg, color-mix(in srgb, rgb(var(--primary-rgb)) 26%, transparent), color-mix(in srgb, rgb(var(--primary-rgb)) 16%, transparent))',
                          'color-mix(in srgb, var(--color-panel2) 68%, transparent)',
                        ].join(', '),
                        border: '1px solid color-mix(in srgb, rgb(var(--primary-rgb)) 45%, white 5%)',
                        boxShadow: '0 8px 28px color-mix(in srgb, rgb(var(--primary-rgb)) 18%, transparent)',
                      } : undefined}
                    >
                      {active ? <span className="wl-nav-edge" aria-hidden="true" /> : null}
                      <Icon size={16} className={cn('shrink-0', active ? 'text-primary' : 'text-muted group-hover:text-secondary')} />
                      <span className="truncate">{l.label}</span>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </nav>
  )

  return (
    <>
      {/* Desktop rail — L10: B10 `.sidebar` 280px surface + gradient (D-02:
          B10 width wins over L7 260px) */}
      <aside
        className={cn(
          'wl-sidebar-surface hidden md:flex flex-col border-r transition-[width] duration-base overflow-hidden',
          'border-border/75',
          collapsed ? 'md:w-[72px]' : 'md:w-[280px]',
        )}
        aria-label="侧边导航"
      >
        <Header isCollapsed={collapsed} />
        {collapsed ? <RailItems /> : <GroupedNav />}
        {!collapsed && (
          <div className="px-3 py-3 text-[10px] font-mono text-muted border-t border-border/55">
            {activeView}
          </div>
        )}
      </aside>

      {/* Mobile overlay drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-black/50" onClick={onCloseMobile} aria-hidden="true" />
          <aside className="ui-drawer-left wl-sidebar-surface relative z-10 flex h-full w-[280px] flex-col border-r border-border/75" aria-label="侧边导航">
            <Header isCollapsed={false} />
            <GroupedNav />
          </aside>
        </div>
      )}
    </>
  )
}

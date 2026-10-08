import * as React from 'react'
import { cn } from '@/lib/utils'
import { VIEW_REGISTRY, OVERVIEW_ID, OVERVIEW_LABEL } from '@/lib/viewRegistry'

/**
 * L10b (2026-09-27): B10 sidebar — the verbatim B10 DOM:
 *
 *   <aside class="sidebar">
 *     <div class="brand">
 *       <div class="brand-mark"></div>
 *       <div><h1>WORK-LAB</h1><small>AI WORKFLOW CONTROL PLANE</small></div>
 *     </div>
 *     <div class="nav">
 *       <button><span class="nav-dot"></span><span>总览</span></button>
 *       …
 *     </div>
 *     <div class="sidebar-footer">
 *       <div class="avatar">A</div>
 *       <div><strong>Alex</strong><small>Personal Workspace</small></div>
 *     </div>
 *   </aside>
 *
 * `.sidebar` (280px gradient rail) / `.brand` / `.brand-mark` (B10's 48px gradient
 * tile, overridden in src/skins/l10b-shell.css to the 91x48 cut-out logo mark — the
 * pinned skin itself stays verbatim per decision D-11) / `.nav button` (+ `.active` gradient + `::before` cyan→blue edge bar) /
 * `.nav-dot` / `.sidebar-footer` / `.avatar` are all B10-verbatim in
 * src/skins/b10.css. This component only supplies the data (the lanes) — the
 * seven NAV_GROUPS (P1-01 invariant) render as the B10 buttons, each group with
 * its own labelled block so all 22 reachable lanes stay one click away.
 *
 * Read-only contract: the rail is pure navigation — no write, approve or
 * configuration affordance exists here.
 */
interface LaneDef {
  id: string
  label: string
}

// L10 (2026-09-27): B07 IA page matrix regrouping — 7 primary nav groups
// covering all 22 reachable lanes exactly once (the P1-01 invariant, now
// including the four B10 lanes: workflows / workflow-editor / observer /
// execution-detail). D3 `work` lane still leads the work group.
export const NAV_GROUPS: { key: string; label: string; ids: string[] }[] = [
  { key: 'home',   label: '首页',   ids: [OVERVIEW_ID] },
  { key: 'work',   label: '工作',   ids: ['work', 'evidence', 'executions', 'task-packs', 'delivery', 'execution-detail'] },
  { key: 'agents', label: '智能体', ids: ['agents'] },
  { key: 'projects', label: '项目', ids: ['projects'] },
  { key: 'gov',    label: '治理',   ids: ['workflows', 'rules-policy', 'approvals', 'audit', 'trust'] },
  { key: 'integrations', label: '集成', ids: ['integrations', 'workflow-editor'] },
  { key: 'system', label: '系统',   ids: ['observer', 'software', 'models', 'monitoring', 'memory', 'tools', 'settings'] },
]

// TASKPACK-UI-20260930: 7-group IA binding verified (home/work/agents/projects/gov/integrations/system).
// All 22 lanes remain reachable (VIEW_REGISTRY unchanged). Observer (observer, rules-policy, audit, approvals, integrations, workflow-editor) stays READ-ONLY: no write/approve/deny/retry/cancel/rollback/install/apply controls exposed in this component; those must be blocked by backend contract and not only hidden here.
// Control/Observer permission matrix (per WORK-LAB contract): only Control Surface executes writes; Observer projection never writes task/state/telemetry.


function buildLanes(): Map<string, LaneDef> {
  const map = new Map<string, LaneDef>([[OVERVIEW_ID, { id: OVERVIEW_ID, label: OVERVIEW_LABEL }]])
  for (const e of VIEW_REGISTRY) {
    if (e.component) map.set(e.id, { id: e.id, label: e.label })
  }
  return map
}

export interface SidebarProps {
  activeView: string
  onSelect: (id: string) => void
}

function Brand() {
  return (
    <div className="brand">
      {/* Decorative on purpose: the h1 below already spells WORK-LAB, so an aria-label here would make
          a screen reader announce the brand twice per render. The glyph is the artwork cut from the
          project logo (see src/assets/brand/work-lab-mark.png); it replaces the "WL" text the pinned
          skin used to show, and the override that sizes it lives in skins/l10b-shell.css. */}
      <div className="brand-mark" aria-hidden="true" />
      <div>
        <h1>WORK-LAB</h1>
        <small>AI WORKFLOW CONTROL PLANE</small>
      </div>
    </div>
  )
}

function Nav({
  activeView,
  onSelect,
}: {
  activeView: string
  onSelect: (id: string) => void
}) {
  const lanes = React.useMemo(buildLanes, [])
  const groups = React.useMemo(
    () =>
      NAV_GROUPS.map((g) => ({
        ...g,
        items: g.ids.map((id) => lanes.get(id)).filter(Boolean) as LaneDef[],
      })).filter((g) => g.items.length > 0),
    [lanes],
  )
  // Scrolling makes a long rail reachable; collapsing is what keeps it short enough to read. The rail is
  // its own scroll box since `36f9a297`, which is necessary but not sufficient — ARIA APG Disclosure
  // Navigation expects each section to be a disclosure button as well, which is the shape Rancher's
  // per-group nav implements and the shape the 23-item rail needs at a 600px-tall window.
  const [collapsed, setCollapsed] = React.useState<ReadonlySet<string>>(() => new Set())
  const toggles = React.useRef<Record<string, HTMLButtonElement | null>>({})
  const setToggleRef = (key: string) => (node: HTMLButtonElement | null) => {
    toggles.current[key] = node
  }
  const toggleGroup = (key: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })

  const onKeyDown = (event: React.KeyboardEvent<HTMLElement>) => {
    if (event.key !== 'Escape') return
    const group = groups.find((g) => g.ids.some((id) => id === activeView))
    const target = event.target as HTMLElement | null
    if (!group || !target || !event.currentTarget.contains(target)) return
    if (target === toggles.current[group.key]) return
    setCollapsed((prev) => (prev.has(group.key) ? prev : new Set(prev).add(group.key)))
    toggles.current[group.key]?.focus()
  }

  return (
    <nav className="nav" onKeyDown={onKeyDown}>
      {groups.map((g) => {
        const open = !collapsed.has(g.key)
        return (
          <div key={g.key} className="flex flex-col gap-1.5 pb-1.5">
            {/* group label (B07 IA matrix) — a disclosure button, so the caption is also the control
                that hides its own items; the muted B10 caption styling is kept in the skin layer */}
            <button
              type="button"
              ref={setToggleRef(g.key)}
              className="nav-group-toggle"
              aria-expanded={open}
              aria-controls={`nav-group-${g.key}`}
              title={open ? `收起 ${g.label}` : `展开 ${g.label}`}
              onClick={() => toggleGroup(g.key)}
            >
              <span className="nav-group-caret" aria-hidden="true" />
              <span className="truncate">{g.label}</span>
            </button>
            {open && (
              <div id={`nav-group-${g.key}`} className="flex flex-col gap-1.5">
                {g.items.map((l) => {
                  const active = activeView === l.id
                  return (
                    <button
                      key={l.id}
                      type="button"
                      onClick={() => onSelect(l.id)}
                      data-lane={l.id}
                      title={l.label}
                      aria-current={active ? 'page' : undefined}
                      className={cn(active && 'active')}
                    >
                      <span className="nav-dot" aria-hidden="true" />
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
}

function SidebarFooter() {
  return (
    <div className="sidebar-footer">
      <div className="avatar">A</div>
      <div>
        <strong>Alex</strong>
        <small>Personal Workspace</small>
      </div>
    </div>
  )
}

export function Sidebar({ activeView, onSelect }: SidebarProps) {
  return (
    <aside className="sidebar sidebar-slot" aria-label="侧边导航">
      <Brand />
      <Nav activeView={activeView} onSelect={onSelect} />
      <SidebarFooter />
    </aside>
  )
}

import { LayoutDashboard, ChevronsLeft, ChevronsRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { VIEW_REGISTRY, OVERVIEW_ID } from '@/lib/viewRegistry'

// U04: navigation is driven by the view registry, not a hardcoded array whose
// index had to line up with a views array in App.tsx. Overview is the synthetic
// landing lane; every registry view is reachable (Delivery/Trust/Settings are
// no longer orphaned).
export function Sidebar({
  activeView,
  onSelect,
  collapsed,
}: {
  activeView: string
  onSelect: (id: string) => void
  collapsed?: boolean
}) {
  const entries = [
    { id: OVERVIEW_ID, label: '总览', icon: LayoutDashboard },
    ...VIEW_REGISTRY.filter((e) => e.component).map((e) => ({ id: e.id, label: e.label, icon: e.icon })),
  ]
  return (
    <div className={cn('flex flex-col items-center py-3 bg-panel border-r border-border transition-all', collapsed ? 'w-12' : 'w-[72px]')}>
      <div className="mb-4 text-xl font-bold" style={{ color: 'var(--accent, #00d4ff)' }}>◈</div>
      <div className="flex flex-col gap-1">
        {entries.map((item) => {
          const Icon = item.icon
          const active = activeView === item.id
          return (
            <button
              key={item.id}
              onClick={() => onSelect(item.id)}
              title={item.label}
              className={cn(
                'w-10 h-10 rounded-md flex items-center justify-center transition-colors',
                active ? 'bg-primary/10 text-primary shadow-[0_0_12px_rgba(0,212,255,0.15)]' : 'text-zinc-500 hover:bg-white/5 hover:text-zinc-300',
              )}
            >
              <Icon size={18} />
            </button>
          )
        })}
      </div>
      <div className="flex-1" />
      <div className="text-[10px] text-zinc-600 font-mono">
        {collapsed ? activeView.slice(0, 2) : activeView}
      </div>
    </div>
  )
}

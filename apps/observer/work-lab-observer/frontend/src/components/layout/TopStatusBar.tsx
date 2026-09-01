import type { ServiceHealth } from '@/types'
import { cn } from '@/lib/utils'

const dot = { healthy: '#00d084', warning: '#ffb020', error: '#ff4d4f' }

export function TopStatusBar({ services }: { services: ServiceHealth[] }) {
  const items = services.length > 0 ? services : [{ name: 'Sidecar', status: 'warning' as const, usage: '离线' }]
  return (
    <div className="h-16 bg-panel2 border-b border-border flex items-center px-4 gap-6 overflow-x-auto">
      {items.map((s) => (
        <div key={s.name} className="flex items-center gap-2 shrink-0">
          <span className="status-pulse" style={{ width: 8, height: 8, borderRadius: '50%', background: dot[s.status] }} />
          <div className="flex flex-col">
            <span className="text-[11px] text-zinc-400 font-medium leading-none">{s.name}</span>
            <span className="text-[10px] text-zinc-600 leading-tight">{s.usage}</span>
          </div>
        </div>
      ))}
      <div className="ml-auto flex items-center gap-2 text-[11px] text-zinc-500">
        <span className={cn('w-2 h-2 rounded-full bg-success status-pulse')} />
        控制塔在线
      </div>
    </div>
  )
}

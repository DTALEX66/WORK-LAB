import { LayoutDashboard, Bot, PlayCircle, Cpu, Brain, Wrench, Activity, Settings, ChevronsLeft, ChevronsRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

const items = [
  { icon: LayoutDashboard, label: '总览' },
  { icon: Bot, label: '智能体' },
  { icon: PlayCircle, label: '执行' },
  { icon: Cpu, label: '模型' },
  { icon: Brain, label: '记忆' },
  { icon: Wrench, label: '工具' },
  { icon: Activity, label: '监控' },
  { icon: Settings, label: '设置' },
]

export function Sidebar({ active, onSelect }: { active: number; onSelect: (i: number) => void }) {
  const [collapsed, setCollapsed] = useState(false)
  return (
    <div className={cn('flex flex-col items-center py-3 bg-panel border-r border-border transition-all', collapsed ? 'w-12' : 'w-[72px]')}>
      <div className="mb-4 text-xl font-bold" style={{ color: '#00d4ff' }}>◈</div>
      {items.map((item, i) => {
        const Icon = item.icon
        return (
          <button
            key={item.label}
            onClick={() => onSelect(i)}
            title={item.label}
            className={cn(
              'w-10 h-10 mb-1 rounded-md flex items-center justify-center transition-colors',
              active === i ? 'bg-primary/10 text-primary shadow-[0_0_12px_rgba(0,212,255,0.15)]' : 'text-zinc-500 hover:bg-white/5 hover:text-zinc-300',
            )}
          >
            <Icon size={18} />
          </button>
        )
      })}
      <div className="flex-1" />
      <button onClick={() => setCollapsed(!collapsed)} className="w-10 h-10 rounded-md flex items-center justify-center text-zinc-600 hover:bg-white/5">
        {collapsed ? <ChevronsRight size={16} /> : <ChevronsLeft size={16} />}
      </button>
    </div>
  )
}

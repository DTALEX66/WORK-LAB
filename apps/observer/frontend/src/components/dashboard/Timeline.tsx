import type { TimelineEvent } from '@/types'
import { Card, CardHeader, CardContent } from '@/components/ui/card'

const colors = { success: '#00d084', running: '#00d4ff', approval: '#ffb020', failed: '#ff4d4f' }

export function Timeline({ events }: { events: TimelineEvent[] }) {
  const items = events.length > 0 ? events : [{ time: '--:--', type: 'running' as const, label: '等待数据…' }]
  return (
    <Card>
      <CardHeader><span>执行时间线</span><span className="text-[11px] text-zinc-500">实时</span></CardHeader>
      <CardContent className="pt-4">
        <div className="relative flex items-center" style={{ height: 44 }}>
          <div className="absolute left-0 right-0 h-px bg-border" />
          {items.map((e, i) => {
            const left = items.length === 1 ? 50 : (i / (items.length - 1)) * 100
            return (
              <div key={i} className="absolute flex flex-col items-center" style={{ left: left + '%', transform: 'translateX(-50%)' }}>
                <span className="relative z-10 w-3 h-3 rounded-full" style={{ background: colors[e.type], boxShadow: '0 0 8px ' + colors[e.type] + '66' }} />
                <span className="mt-1.5 text-[10px] text-zinc-500 tabular-nums">{e.time}</span>
                <span className="text-[10px] text-zinc-400 whitespace-nowrap max-w-[120px] truncate">{e.label}</span>
              </div>
            )
          })}
        </div>
        <div className="mt-4 flex items-center gap-4 text-[10px] text-zinc-500">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ background: '#00d084' }} />成功</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ background: '#00d4ff' }} />运行中</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ background: '#ffb020' }} />需审批</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ background: '#ff4d4f' }} />失败</span>
        </div>
      </CardContent>
    </Card>
  )
}

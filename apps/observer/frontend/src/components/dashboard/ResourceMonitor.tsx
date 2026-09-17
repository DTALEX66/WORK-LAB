import { Card, CardHeader, CardContent } from '@/components/ui/card'
import type { SysResources } from '@/lib/api'

function fmtNet(b: number): string { return b >= 1e9 ? (b / 1e9).toFixed(1) + ' GB' : (b / 1e6).toFixed(0) + ' MB' }

export function ResourceMonitor({ resources }: { resources: SysResources | null }) {
  const items = resources
    ? [
        { label: 'CPU', value: Math.round(resources.cpu), text: Math.round(resources.cpu) + '%' },
        { label: '内存', value: Math.round(resources.mem), text: Math.round(resources.mem) + '%' },
        { label: '磁盘', value: Math.round(resources.disk), text: Math.round(resources.disk) + '%' },
        { label: '网络', value: 0, text: '↑' + fmtNet(resources.netSent) },
      ]
    : [
        { label: 'CPU', value: 0, text: '—' },
        { label: '内存', value: 0, text: '—' },
        { label: '磁盘', value: 0, text: '—' },
        { label: '网络', value: 0, text: '—' },
      ]
  return (
    <Card>
      <CardHeader><span>资源监控</span><span className="text-[11px] text-zinc-500">{resources ? '真实' : '等待数据'}</span></CardHeader>
      <CardContent className="grid grid-cols-4 gap-3">
        {items.map((r) => {
          const c = r.value > 85 ? '#ff4d4f' : r.value > 60 ? '#ffb020' : '#00d084'
          const dash = 2 * Math.PI * 22
          return (
            <div key={r.label} className="flex flex-col items-center gap-1.5">
              {r.value > 0 ? (
                <svg width={56} height={56} viewBox="0 0 56 56">
                  <circle cx={28} cy={28} r={22} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={5} />
                  <circle cx={28} cy={28} r={22} fill="none" stroke={c} strokeWidth={5} strokeLinecap="round"
                    strokeDasharray={dash} strokeDashoffset={dash * (1 - r.value / 100)} transform="rotate(-90 28 28)" />
                </svg>
              ) : (
                <div className="flex items-center justify-center" style={{ width: 56, height: 56 }}><span className="text-[10px] text-zinc-500">—</span></div>
              )}
              <div className="text-center">
                <div className="text-sm font-semibold tabular-nums" style={{ color: r.value > 0 ? c : '#71717a' }}>{r.text}</div>
                <div className="text-[10px] text-zinc-500">{r.label}</div>
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}

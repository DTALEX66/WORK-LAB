import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { SnapshotV3 } from '@/types'
import { fmtTokens, fmtCostQuality, activityTone } from '@/lib/api'

// U07: per-project panel reading the REAL v3 `projects[]` projection.
// activityState is real (ACTIVE/REGISTERED/IDLE/UNKNOWN); git dirty is the
// real counter; token/costQuality is the backend label (no fabricated cost).
export function ProjectPanel({ snap }: { snap: SnapshotV3 | null }) {
  const projects = snap?.projects || []
  return (
    <Card>
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border text-sm font-medium">
        <span>项目</span>
        <span className="text-[11px] text-zinc-500">{snap ? projects.length + ' 个 · 真实' : '等待数据'}</span>
      </div>
      <div className="p-0">
        {projects.length === 0 ? (
          <div className="p-6 text-center text-zinc-500 text-xs">{snap ? 'registry 为空（UNKNOWN）' : '数据源未接入'}</div>
        ) : (
          <div className="flex flex-col">
            {projects.slice(0, 8).map((p) => {
              const tone = activityTone(p.activityState)
              const dirty = p.git.dirtyCount
              return (
                <div key={p.projectId} className="px-4 py-2.5 border-b border-border/40 last:border-0">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium truncate">{p.displayName || p.projectId}</span>
                    <Badge variant={tone === 'active' ? 'success' : 'muted'}>{p.activityState || 'UNKNOWN'}</Badge>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[10px] text-zinc-500">
                    <span className="font-mono">{p.agentPlatform || '—'}</span>
                    <span className="tabular-nums">
                      {p.activeExecutionCount} 执行 · {fmtTokens(p.token.totalTokens)} <span className="text-zinc-600">{fmtCostQuality(p.token.costQuality)}</span>
                    </span>
                  </div>
                  <div className="mt-1 flex items-center gap-2 text-[10px] text-zinc-600 font-mono">
                    <span>{p.git.branch || '—'}@{p.git.localSha ? p.git.localSha.slice(0, 7) : '—'}</span>
                    {dirty ? <Badge variant="warning">脏 {dirty}</Badge> : <Badge variant="muted">干净</Badge>}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </Card>
  )
}

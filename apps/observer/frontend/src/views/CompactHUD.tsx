
// U05 (taskpack 20260919): Compact is a DEDICATED HUD, not just a narrow full
// layout. Single column, no sidebar, dense 4-KPI strip + one live truth row,
// 320px-safe. Reads the REAL v3 transport/token/coverage truth; UNKNOWN when
// there is no data (no fabricated 0 / "online").
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { SnapshotV3 } from '@/types'
import { fmtTokens, fmtCostQuality, tokenTruth, snapshotToTransportTruth } from '@/lib/api'

export function CompactHUD({ snap, live }: { snap: SnapshotV3 | null; live: boolean }) {
  const tt = tokenTruth(snap)
  const tr = snapshotToTransportTruth(snap)
  const kpis = [
    { k: '传输', v: live ? 'LIVE' : (tr ? tr.transportState : 'UNKNOWN') },
    { k: '项目', v: snap ? String(snap.projects.length) : 'UNKNOWN' },
    { k: 'Token', v: snap ? fmtTokens(tt?.totalTokens ?? null) : 'UNKNOWN' },
    { k: '质量', v: fmtCostQuality(tt?.costQuality) },
  ]
  return (
    <div className="compact-hud h-full overflow-auto p-3 text-ink">
      <div className="grid grid-cols-4 gap-2 mb-3">
        {kpis.map((x) => (
          <div key={x.k} className="panel2 rounded p-2 text-center min-w-0">
            <div className="text-[10px] text-zinc-500">{x.k}</div>
            <div className="text-sm font-bold tabular-nums truncate">{x.v}</div>
          </div>
        ))}
      </div>
      <Card>
        <div className="flex items-center justify-between px-3 py-2 text-[11px]">
          <Badge variant={live ? 'success' : tr && tr.transportState === 'OFFLINE' ? 'error' : 'muted'}>
            {live ? 'LIVE' : (tr ? tr.transportState : 'UNKNOWN')}
          </Badge>
          <span className="text-zinc-500 tabular-nums">
            {tr && tr.coverageNumerator != null
              ? '覆盖 ' + tr.coverageNumerator + '/' + (tr.coverageDenominator ?? '?')
              : '覆盖 UNKNOWN'}
          </span>
          <span className="text-zinc-600 font-mono">{snap ? 'rev ' + snap.revision : '—'}</span>
        </div>
      </Card>
    </div>
  )
}


// U05 (taskpack 20260919) · L10b (2026-09-27): Compact is a DEDICATED HUD, not
// just a narrow full layout. Single column, no sidebar, dense KPI strip + one
// live truth row, 320px-safe. Reads the REAL v3 transport/token/coverage truth;
// UNKNOWN when there is no data (no fabricated 0 / "online").
//
// L10b: the strip uses the B10 `.kpi-grid` of `.panel.kpi` cells (35px primary
// numbers) and the truth row the B10 `.panel` + `.status-stack` `.tag` pills.
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
    <div className="compact-hud text-ink">
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, minmax(0, 1fr))' }}>
        {kpis.map((x) => (
          <div key={x.k} className="panel kpi">
            <strong className="truncate text-[22px]">{x.v}</strong>
            <small>{x.k}</small>
          </div>
        ))}
      </div>
      <Card className="mt-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Badge variant={live ? 'success' : tr && tr.transportState === 'OFFLINE' ? 'error' : 'muted'}>
            {live ? 'LIVE' : (tr ? tr.transportState : 'UNKNOWN')}
          </Badge>
          <span className="tabular-nums text-muted">
            {tr && tr.coverageNumerator != null
              ? '覆盖 ' + tr.coverageNumerator + '/' + (tr.coverageDenominator ?? '?')
              : '覆盖 UNKNOWN'}
          </span>
          <span className="font-mono text-muted">{snap ? 'rev ' + snap.revision : '—'}</span>
        </div>
      </Card>
    </div>
  )
}

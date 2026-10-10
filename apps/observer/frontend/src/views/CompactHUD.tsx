
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
import { fmtTokens, fmtCostQuality, tokenTruth, snapshotToTransportTruth, frontTransportState } from '@/lib/api'

export function CompactHUD({ snap, live, error = null }: {
  snap: SnapshotV3 | null; live: boolean; error?: string | null
}) {
  const tt = tokenTruth(snap)
  const tr = snapshotToTransportTruth(snap)
  // The HUD's own status word: a snapshot keeps whatever transportState it was
  // read with, so replaying it after the read path fails would claim a live
  // connection the browser no longer has.
  const transport = frontTransportState(snap, live, error)
  const kpis = [
    { k: '传输', v: transport },
    { k: '项目', v: snap ? String(snap.projects.length) : 'UNKNOWN' },
    { k: 'Token', v: snap ? fmtTokens(tt?.totalTokens ?? null) : 'UNKNOWN' },
    { k: '质量', v: fmtCostQuality(tt?.costQuality) },
  ]
  return (
    <div className="compact-hud text-ink">
      {/* N-2: the shell owns the grid. The inline `repeat(4, minmax(0,1fr))`
          overrode l10b-shell.css's fluid `auto-fit minmax(max(150px,20cqi),1fr)`
          and its `@container page (max-width: 820px)` collapse to two columns,
          so at the 320px width this file claims to be safe for, four tracks got
          ~70px each and clipped. Deleting the override makes the claim true. */}
      <div className="kpi-grid">
        {kpis.map((x) => (
          <div key={x.k} className="panel kpi">
            <strong className="truncate text-[22px]">{x.v}</strong>
            <small>{x.k}</small>
          </div>
        ))}
      </div>
      <Card className="mt-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Badge variant={transport === 'LIVE' ? 'success' : transport === 'OFFLINE' ? 'error' : 'muted'}>
            {transport}
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

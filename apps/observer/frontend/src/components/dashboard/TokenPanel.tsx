import { Card } from '@/components/ui/card'
import type { SnapshotV3 } from '@/types'
import { fmtTokens, fmtCostQuality, tokenTruth } from '@/lib/api'

// U07: token panel reads the REAL v3 `tokenSummary` (the only token+quality
// truth). No fabricated cost line, no quota, no FX. Nulls render UNKNOWN.
export function TokenPanel({ snap }: { snap: SnapshotV3 | null }) {
  const tt = tokenTruth(snap)
  const inT = tt?.inputTokens ?? null
  const outT = tt?.outputTokens ?? null
  const total = tt?.totalTokens ?? null
  const max = Math.max(inT ?? 0, outT ?? 0, 1)
  // B5: a progress bar needs a REAL source. The value text is always shown
  // honestly (fmtTokens(null) -> UNKNOWN, never "0"); the percentage bar is
  // only drawn when at least one real token figure exists. No token data ->
  // no fabricated 0% bar, just the UNKNOWN values + the real state.
  const hasToken = inT != null || outT != null || total != null
  return (
    <Card>
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border text-sm font-medium">
        <span>Token</span>
        <span className="text-[11px] text-zinc-500">质量 {fmtCostQuality(tt?.costQuality)}</span>
      </div>
      <div className="p-4 flex flex-col gap-3">
        {[
          { label: '输入', value: inT, color: 'rgb(var(--primary-rgb))' },
          { label: '输出', value: outT, color: 'rgb(var(--secondary-rgb))' },
        ].map((d) => (
          <div key={d.label}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-zinc-400">{d.label}</span>
              <span className="tabular-nums text-zinc-200">{fmtTokens(d.value)}</span>
            </div>
            {hasToken && (
              <div className="h-2 rounded-full bg-zinc-700/50 overflow-hidden">
                <div className="h-full rounded-full" style={{ width: (max ? ((d.value ?? 0) / max) * 100 : 0) + '%', background: d.color }} />
              </div>
            )}
          </div>
        ))}
        <div className="flex justify-between text-xs text-zinc-400 pt-1">
          <span>总计</span>
          <span className="tabular-nums text-zinc-200">{fmtTokens(total)}</span>
        </div>
        {!hasToken && (
          <p className="text-[11px] text-zinc-500">
            无 token 数据{snap ? ' · 快照已接入但 token 未知' : ' · 数据源未接入'}（不估算、不伪造 0%）
          </p>
        )}
        <p className="text-[10px] text-zinc-600">成本质量（EXACT/ESTIMATED/UNKNOWN）由后端投影，前端不估算金额、汇率或配额。</p>
      </div>
    </Card>
  )
}

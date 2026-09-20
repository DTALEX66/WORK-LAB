import { Moon, Sun, PanelsTopLeft, PanelTop } from 'lucide-react'
import type { SnapshotV3 } from '@/types'
import type { ThemeMode, LayoutMode, LiveSnapshotState } from '@/lib/api'

// U07: the top bar shows the REAL transport truth. The legacy bar ALWAYS lit a
// green "控制塔在线" dot — a fabricated "online". Now the indicator reflects
// transportState: only LIVE is green; everything else is honest.
//
// U05: theme + layout cycle controls (dark/light, full/compact) are real and
// URL-driven.
export function TopStatusBar({
  snap,
  source,
  live,
  theme,
  layout,
  onCycleTheme,
  onCycleLayout,
}: {
  snap: SnapshotV3 | null
  source: LiveSnapshotState['source']
  live: boolean
  theme: ThemeMode
  layout: LayoutMode
  onCycleTheme: () => void
  onCycleLayout: () => void
}) {
  const ts = snap?.transport.transportState
  const freshness = snap?.transport.freshnessState
  const cov = snap?.coverage
  const dot =
    live || ts === 'LIVE' ? '#00d084' :
    ts === 'OFFLINE' ? '#ff4d4f' :
    ts ? '#ffb020' : '#71717a'
  const stateText = live ? 'LIVE' : (ts || 'UNKNOWN')
  return (
    <div className="h-16 bg-panel2 border-b border-border flex items-center px-4 gap-5 overflow-x-auto">
      <div className="flex items-center gap-2 shrink-0">
        <span className="status-pulse" style={{ width: 8, height: 8, borderRadius: '50%', background: dot }} />
        <div className="flex flex-col">
          <span className="text-[11px] text-zinc-200 font-medium leading-none">{stateText}</span>
          <span className="text-[10px] text-zinc-600 leading-tight">
            {freshness ? '新鲜度 ' + freshness : '未知新鲜度'} · {source}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-1.5 shrink-0 text-[10px] text-zinc-500">
        <span>覆盖</span>
        <span className="tabular-nums text-zinc-300">
          {cov && cov.numerator != null
            ? cov.numerator + '/' + (cov.denominator ?? '?') + (cov.scope ? ' · ' + cov.scope : '')
            : 'UNKNOWN'}
        </span>
      </div>
      {snap && (
        <div className="flex items-center gap-1.5 shrink-0 text-[10px] text-zinc-500">
          <span>revision</span>
          <span className="tabular-nums text-zinc-300">{String(snap.revision)}</span>
        </div>
      )}
      <div className="ml-auto flex items-center gap-1.5 shrink-0">
        <button
          onClick={onCycleLayout}
          title={layout === 'full' ? '紧凑布局' : '完整布局'}
          className="w-7 h-7 rounded-md flex items-center justify-center text-zinc-400 hover:bg-white/5"
        >
          {layout === 'full' ? <PanelTop size={14} /> : <PanelsTopLeft size={14} />}
        </button>
        <button
          onClick={onCycleTheme}
          title={theme === 'dark' ? '浅色' : '深色'}
          className="w-7 h-7 rounded-md flex items-center justify-center text-zinc-400 hover:bg-white/5"
        >
          {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
        </button>
        <span className="text-[11px] text-zinc-500 ml-1">
          {live ? 'LIVE' : (snap ? '非 LIVE' : '未接入')}
        </span>
      </div>
    </div>
  )
}

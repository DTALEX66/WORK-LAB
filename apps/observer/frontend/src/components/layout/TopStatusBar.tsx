import { Search } from 'lucide-react'
import { WindowControls } from '@/components/layout/WindowControls'
import { THEMES } from '@/theme/tokens'
import type { SnapshotV3 } from '@/types'
import type { ThemeMode, LayoutMode, LiveSnapshotState } from '@/lib/api'

/**
 * L10b (2026-09-27): B10 top bar — the verbatim B10 structure:
 *
 *   <header class="topbar">
 *     <div class="search" id="openPalette">⌘ K　搜索页面 / 命令 / 资源</div>
 *     <div class="top-actions">
 *       <button class="ghost-btn">通知</button>
 *       <button class="ghost-btn">工作区</button>
 *     </div>
 *   </header>
 *
 * `.topbar` (78px) / `.search` (min(620px,54vw), 14px radius) / `.top-actions` /
 * `.ghost-btn` are B10-verbatim in src/skins/b10.css. The transport dot +
 * freshness + coverage + revision remain the REAL backend truth (U07
 * discipline — only LIVE is green, everything else honest); they render as an
 * inline truth strip inside the search field's row, so the B10 silhouette is
 * preserved without inventing status.
 *
 * The pinned search label ("搜索或命令…" + "Ctrl K") is a CI contract — it is
 * kept verbatim; B10 only wins for structure/style.
 */
export function TopStatusBar({
  snap,
  source,
  live,
  theme,
  layout,
  onCycleTheme,
  onCycleLayout,
  onOpenSearch,
  onOpenDrawer,
  onNotify,
}: {
  snap: SnapshotV3 | null
  source: LiveSnapshotState['source']
  live: boolean
  theme: ThemeMode
  layout: LayoutMode
  onCycleTheme: () => void
  onCycleLayout: () => void
  /** opens the CommandPalette (Ctrl/Cmd+K global shortcut also wired in App) */
  onOpenSearch?: () => void
  /** opens the B10 `.drawer` (workspace / context) */
  onOpenDrawer?: () => void
  /** B10 `.toast` notification (1800ms auto-hide) */
  onNotify?: () => void
}) {
  const ts = snap?.transport.transportState
  const freshness = snap?.transport.freshnessState
  const cov = snap?.coverage
  const palette = THEMES[theme].colors
  const dotHex =
    live || ts === 'LIVE' ? palette.successHex :
    ts === 'OFFLINE' ? palette.errorHex :
    ts ? palette.warningHex : palette.muted
  const dotStyle = { width: 8, height: 8, borderRadius: '50%', background: dotHex }
  const stateText = live ? 'LIVE' : (ts || 'UNKNOWN')
  const coverageText =
    cov && cov.numerator != null
      ? cov.numerator + '/' + (cov.denominator ?? '?') + (cov.scope ? ' · ' + cov.scope : '')
      : 'UNKNOWN'

  return (
    <header className="topbar">
      {/* B10 brand lockup, reduced to a chip. This is not decoration: the
          compact HUD renders no rail, so without it the floating panel has no
          identity at all, and the main window runs with `decorations:false` —
          this row IS the chrome. Colors come from the skin's own --primary /
          --secondary, never a literal here (G2). */}
      <span className="topbar-brand" data-testid="topbar-brand">
        <span className="topbar-brand-mark" aria-hidden="true" />
        <span className="topbar-brand-word">WORK-LAB</span>
      </span>

      {/* B10 `.search` — the primary search affordance (opens the palette) */}
      {onOpenSearch && (
        <div
          role="button"
          tabIndex={0}
          onClick={onOpenSearch}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              onOpenSearch()
            }
          }}
          className="search"
          aria-label="搜索或命令"
        >
          <Search size={15} aria-hidden="true" />
          <span className="truncate">搜索或命令…</span>
          <kbd className="ml-auto shrink-0 rounded border border-border bg-panel2 px-1.5 py-0.5 text-[9px] text-muted">
            Ctrl K
          </kbd>
        </div>
      )}

      {/* honest transport truth strip (REAL v3 fields only). Shrinks instead of
          forcing the action buttons into one-glyph columns. */}
      <div className="truth-strip hidden items-center gap-3 text-[10px] text-muted lg:flex">
        <span className="flex items-center gap-2">
          <span className="status-pulse shrink-0" style={dotStyle} aria-hidden="true" />
          <span className="font-medium text-ink">{stateText}</span>
          <span>{freshness ? '新鲜度 ' + freshness : '未知新鲜度'} · {source}</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span>覆盖</span>
          <span className="tabular-nums text-ink">{coverageText}</span>
        </span>
        {snap && (
          <span className="flex items-center gap-1.5">
            <span>revision</span>
            <span className="tabular-nums text-ink">{String(snap.revision)}</span>
          </span>
        )}
      </div>

      {/* Custom title bar: both windows set decorations:false, so this strip is
          the only drag surface the shell has. */}
      <div className="drag-region" data-tauri-drag-region aria-hidden="true" />

      <div className="top-actions">
        <button type="button" className="ghost-btn" onClick={onNotify}>
          通知
        </button>
        <button type="button" className="ghost-btn" onClick={onOpenDrawer}>
          工作区
        </button>
        <button
          type="button"
          className="ghost-btn"
          onClick={onCycleLayout}
          title={layout === 'full' ? '紧凑布局' : '完整布局'}
          aria-label={layout === 'full' ? '切换到紧凑布局' : '切换到完整布局'}
        >
          {layout === 'full' ? '紧凑' : '完整'}
        </button>
        <button
          type="button"
          className="ghost-btn"
          onClick={onCycleTheme}
          title={theme === 'dark' ? '浅色主题' : '深色主题'}
          aria-label={theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'}
        >
          {theme === 'dark' ? '浅色' : '深色'}
        </button>
      </div>

      <WindowControls />
    </header>
  )
}

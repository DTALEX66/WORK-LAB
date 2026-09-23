import { Moon, Sun, PanelsTopLeft, PanelTop, Search, Bell, Menu } from 'lucide-react'
import type { SnapshotV3 } from '@/types'
import type { ThemeMode, LayoutMode, LiveSnapshotState } from '@/lib/api'
import { cn } from '@/lib/utils'

/**
 * UI_SHELL (20260921): top bar with a global search affordance that opens
 * the CommandPalette (L6: Ctrl/Cmd+K). The transport dot + freshness +
 * coverage + revision remain the REAL backend truth (U07 discipline —
 * only LIVE is green, everything else honest). A mobile menu button opens
 * the Sidebar overlay drawer.
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
  onOpenMobileNav,
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
  /** opens the mobile sidebar drawer (<768px) */
  onOpenMobileNav?: () => void
}) {
  const ts = snap?.transport.transportState
  const freshness = snap?.transport.freshnessState
  const cov = snap?.coverage
  const dotHex =
    live || ts === 'LIVE' ? '#22C55E' :
    ts === 'OFFLINE' ? '#EF4444' :
    ts ? '#F59E0B' : '#8EABBC'
  const dotStyle = { width: 8, height: 8, borderRadius: '50%', background: dotHex }
  const stateText = live ? 'LIVE' : (ts || 'UNKNOWN')

  return (
    <div className="h-14 bg-panel2 border-b border-border flex items-center gap-3 px-3 sm:px-4 overflow-x-auto">
      {/* mobile nav trigger */}
      {onOpenMobileNav && (
        <button
          type="button"
          onClick={onOpenMobileNav}
          aria-label="打开导航"
          className="md:hidden h-8 w-8 shrink-0 rounded-md flex items-center justify-center text-muted hover:bg-panel hover:text-ink transition-colors duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
        >
          <Menu size={16} />
        </button>
      )}

      <div className="flex items-center gap-2 shrink-0">
        <span
          className="status-pulse shrink-0"
          style={dotStyle}
          aria-hidden="true"
        />
        <div className="flex flex-col">
          <span className="text-[11px] text-ink font-medium leading-none">{stateText}</span>
          <span className="text-[10px] text-muted leading-tight">
            {freshness ? '新鲜度 ' + freshness : '未知新鲜度'} · {source}
          </span>
        </div>
      </div>

      <div className="hidden sm:flex items-center gap-1.5 shrink-0 text-[10px] text-muted">
        <span>覆盖</span>
        <span className="tabular-nums text-ink">
          {cov && cov.numerator != null
            ? cov.numerator + '/' + (cov.denominator ?? '?') + (cov.scope ? ' · ' + cov.scope : '')
            : 'UNKNOWN'}
        </span>
      </div>
      {snap && (
        <div className="hidden sm:flex items-center gap-1.5 shrink-0 text-[10px] text-muted">
          <span>revision</span>
          <span className="tabular-nums text-ink">{String(snap.revision)}</span>
        </div>
      )}

      <div className="ml-auto flex items-center gap-1.5 shrink-0">
        {/* global search affordance → CommandPalette */}
        {onOpenSearch && (
          <button
            type="button"
            onClick={onOpenSearch}
            className={cn(
              'hidden md:flex items-center gap-2 h-8 rounded-md border border-border bg-panel px-3 text-[11px] text-muted transition-colors duration-fast',
              'hover:text-ink hover:border-secondary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
            )}
          >
            <Search size={13} aria-hidden="true" />
            <span>搜索或命令…</span>
            <kbd className="rounded border border-border bg-panel2 px-1 py-0.5 text-[9px] text-muted">
              Ctrl K
            </kbd>
          </button>
        )}
        {/* notification indicator = transport state (honest, not a fake bell count) */}
        <span title={live ? 'LIVE 数据源在线' : '数据源非 LIVE'}>
          <Bell size={15} className="text-muted" aria-hidden="true" />
        </span>
        <button
          type="button"
          onClick={onCycleLayout}
          title={layout === 'full' ? '紧凑布局' : '完整布局'}
          className="h-8 w-8 rounded-md flex items-center justify-center text-muted hover:bg-panel hover:text-ink transition-colors duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
        >
          {layout === 'full' ? <PanelTop size={14} /> : <PanelsTopLeft size={14} />}
        </button>
        <button
          type="button"
          onClick={onCycleTheme}
          title={theme === 'dark' ? '浅色主题' : '深色主题'}
          className="h-8 w-8 rounded-md flex items-center justify-center text-muted hover:bg-panel hover:text-ink transition-colors duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
        >
          {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
        </button>
        <span className="hidden sm:inline text-[11px] text-muted ml-1">
          {live ? 'LIVE' : (snap ? '非 LIVE' : '未接入')}
        </span>
      </div>
    </div>
  )
}

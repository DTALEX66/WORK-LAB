import { useState, useEffect, useMemo, useCallback } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopStatusBar } from '@/components/layout/TopStatusBar'
import { KPICard } from '@/components/dashboard/KPICard'
import { ExecutionTable } from '@/components/dashboard/ExecutionTable'
import { ProjectPanel } from '@/components/dashboard/ProjectPanel'
import { TokenPanel } from '@/components/dashboard/TokenPanel'
import { CommandPalette, type PaletteItem } from '@/components/ui/command-palette'
import {
  MonitoringView, TrustView, SettingsView,
} from '@/views/Views'
import { CompactHUD } from '@/views/CompactHUD'
import {
  useLiveSnapshot, fmtCostQuality, tokenTruth, executionsToRows,
  type ThemeMode, type LayoutMode,
} from '@/lib/api'
import { VIEW_REGISTRY, OVERVIEW_ID } from '@/lib/viewRegistry'
import { announce } from '@/lib/a11y'

type ViewId = string

// U04/U05: the active view + theme are driven by URL params (?view=, ?theme=,
// ?layout=) so the dashboard is deep-linkable and Full/Compact/Dark/Light is
// real, not a hardcoded class. The default landing view is the Overview panel.
function readInitialView(): ViewId {
  try {
    const v = new URLSearchParams(window.location.search).get('view')
    if (v && (VIEW_REGISTRY.some((e) => e.id === v) || v === OVERVIEW_ID)) return v
  } catch { /* no URL (SSR/test) -> default */ }
  return OVERVIEW_ID
}

function readInitialTheme(): ThemeMode {
  try {
    const t = new URLSearchParams(window.location.search).get('theme')
    if (t === 'light' || t === 'dark') return t
  } catch { /* ignore */ }
  return 'dark'
}

function readInitialLayout(): LayoutMode {
  try {
    const s = new URLSearchParams(window.location.search)
    const l = s.get('layout')
    if (l === 'full' || l === 'compact') return l
    // B2: the legacy tauri.conf.json entry contract picks the LAYOUT via
    // view=full|compact (not a lane). Honor it as a layout alias so the
    // floating panel (?view=compact) really renders the Compact HUD and old
    // saved links keep working; `layout=` stays the canonical param that the
    // URL write-back persists on navigation.
    const v = s.get('view')
    if (v === 'full' || v === 'compact') return v
  } catch { /* no URL (SSR/test) -> default */ }
  return 'full'
}

export default function App() {
  const [view, setView] = useState<ViewId>(readInitialView)
  const [theme, setTheme] = useState<ThemeMode>(readInitialTheme)
  const [layout, setLayout] = useState<LayoutMode>(readInitialLayout)
  // U06/SSE: live snapshot — first poll + server-sent events, no fixed ports.
  const { snap, source, live, error } = useLiveSnapshot()

  // UI_SHELL (20260921): desktop rail collapse + mobile drawer + command palette.
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [paletteOpen, setPaletteOpen] = useState(false)

  const openPalette = useCallback(() => setPaletteOpen(true), [])
  const closePalette = useCallback(() => setPaletteOpen(false), [])

  // L6 keyboard authority: global Ctrl/Cmd+K toggles the command palette.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setPaletteOpen((o) => !o)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // CommandPalette items = every reachable view (jump = setView) plus the
  // theme/layout actions. Deep-link mechanism (?view=/theme=/layout=) is
  // unchanged — selecting just calls setView, which the existing URL writer
  // (useEffect below) persists.
  const paletteItems = useMemo<PaletteItem[]>(() => {
    const viewItems: PaletteItem[] = [
      { id: 'nav-overview', label: '总览', group: '跳转', run: () => setView(OVERVIEW_ID) },
      ...VIEW_REGISTRY.map((e): PaletteItem => ({
        id: 'nav-' + e.id,
        label: e.label,
        group: '跳转',
        run: () => setView(e.id),
      })),
    ]
    const actions: PaletteItem[] = [
      {
        id: 'act-theme',
        label: theme === 'dark' ? '切换到浅色主题' : '切换到深色主题',
        group: '动作',
        run: () => setTheme((t) => (t === 'dark' ? 'light' : 'dark')),
      },
      {
        id: 'act-layout',
        label: layout === 'full' ? '切换到紧凑布局' : '切换到完整布局',
        group: '动作',
        run: () => setLayout((l) => (l === 'full' ? 'compact' : 'full')),
      },
      {
        id: 'act-rail',
        label: sidebarCollapsed ? '展开侧边导航' : '折叠侧边导航',
        group: '动作',
        run: () => setSidebarCollapsed((c) => !c),
      },
    ]
    return [...viewItems, ...actions]
  }, [theme, layout, sidebarCollapsed])

  // U05/B3: theme is projected through the SAME contract as the pre-render
  // script in index.html — the CSS defines :root (dark default) + html.light
  // and has NO .dark rule, so the old .dark class toggle was a visual no-op.
  // Unify: toggle .light + colorScheme, exactly like index.html does.
  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle('light', theme === 'light')
    root.style.colorScheme = theme === 'light' ? 'light' : 'dark'
  }, [theme])

  // UI_SHELL (20260921): keep the deep-link (?view=/?theme=/?layout=) in sync
  // so refreshing / sharing a URL preserves the active view + theme + layout.
  // This extends (does not change) the existing read-only deep-link init.
  useEffect(() => {
    if (typeof window === 'undefined') return
    const p = new URLSearchParams()
    if (view !== OVERVIEW_ID) p.set('view', view)
    if (theme !== 'dark') p.set('theme', theme)
    if (layout !== 'full') p.set('layout', layout)
    // B4: keep the validated data-source param (?api=) that the Tauri shell
    // injects — api.ts loadRuntimeDescriptor() reads it at module init, so
    // dropping it on navigation/refresh would silently fall back to the
    // non-authoritative static-preview default. Only a present, non-empty api
    // is preserved; other runtime params are not blindly carried.
    const api = new URLSearchParams(window.location.search).get('api')
    if (api) p.set('api', api)
    const qs = p.toString()
    const url = window.location.pathname + (qs ? '?' + qs : '')
    window.history.replaceState(null, '', url)
  }, [view, theme, layout])

  const isOverview = view === OVERVIEW_ID
  const tt = tokenTruth(snap)
  const rows = executionsToRows(snap)
  // REAL v3 KPIs (no phantom agents/models/resources):
  const activeExecs = rows.filter((r) => r.state === 'RUNNING' || r.state === 'STARTING').length

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))
  const toggleLayout = () => setLayout((l) => (l === 'full' ? 'compact' : 'full'))
  const isCompact = layout === 'compact'

  // U03/WlA11y parity: announce theme transitions to assistive tech (the static
  // web/ surface did this via WlA11y.announce on theme switch).
  useEffect(() => {
    announce(theme === 'dark' ? '已切换为深色主题' : '已切换为浅色主题')
  }, [theme])

  // U03/WlA11y parity: announce data-source transitions (LIVE / STALE /
  // OFFLINE) — the four state words the static surface announced verbatim.
  useEffect(() => {
    if (error && !snap) {
      announce('实时数据不可用，界面显示 OFFLINE（不加载假数据）')
    } else if (live) {
      announce('已加载实时投影数据')
    } else if (snap && source === 'stale') {
      announce('实时数据不可用，已保留上次良好投影（last-good，标记为 STALE）')
    }
  }, [snap, source, live, error])

  const mainContent = (
    error && !snap ? (
      <div className="max-w-xl mx-auto mt-10 panel2 rounded-md p-6 text-center">
        <div className="text-lg text-error mb-2">数据源不可用</div>
        <p className="text-xs text-zinc-500 whitespace-pre-wrap">{error}</p>
        <p className="text-[11px] text-zinc-600 mt-3">
          保持 UNKNOWN 真相 — 不伪造 Agent / 模型 / 成本 / 资源
        </p>
      </div>
    ) : isOverview ? (
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-4 gap-4">
          <KPICard
            title="项目"
            value={snap ? String(snap.projects.length) : 'UNKNOWN'}
            sub={snap ? 'registry' : '数据源未接入'}
          />
          <KPICard
            title="活跃执行"
            value={snap ? String(activeExecs) : 'UNKNOWN'}
            sub={'共 ' + (snap ? String(rows.length) : '—') + ' 条'}
          />
          <KPICard
            title="Token"
            value={snap ? fmtTokensSafe(tt) : 'UNKNOWN'}
            sub={'质量 ' + fmtCostQuality(tt?.costQuality)}
          />
          <KPICard
            title="数据源"
            value={live ? 'LIVE' : snap ? source.toUpperCase() : 'UNKNOWN'}
            sub={snap ? ('revision ' + String(snap.revision)) : '等待数据'}
          />
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2 panel2 rounded-md p-4 min-h-[300px]">
            <ExecutionTable rows={snap ? rows : []} hasData={!!snap} />
          </div>
          <div className="flex flex-col gap-4">
            <ProjectPanel snap={snap} />
            <TokenPanel snap={snap} />
          </div>
        </div>
      </div>
    ) : view === 'monitoring' ? (
      <MonitoringView snap={snap} />
    ) : view === 'trust' ? (
      <TrustView snap={snap} />
    ) : view === 'settings' ? (
      <SettingsView snap={snap} />
    ) : (
      (() => {
        const entry = VIEW_REGISTRY.find((e) => e.id === view)
        if (!entry || !entry.component) {
          // Unknown view id (bad URL) -> fall back to Overview; never a
          // silent false view.
          setView(OVERVIEW_ID)
          return null
        }
        const C = entry.component
        return <C snap={snap} />
      })()
    )
  )

  // U05: compact is a DEDICATED HUD — no sidebar, single column, 320px-safe.
  // full keeps the sidebar + multi-panel layout.
  if (isCompact) {
    return (
      <div data-layout={layout} className="flex h-screen overflow-hidden text-ink">
        <div className="flex-1 flex flex-col min-w-0">
          <TopStatusBar
            snap={snap}
            source={source}
            live={live}
            theme={theme}
            layout={layout}
            onCycleTheme={toggleTheme}
            onCycleLayout={toggleLayout}
            onOpenSearch={openPalette}
          />
          <div className="flex-1">
            <CompactHUD snap={snap} live={live} />
          </div>
        </div>
        <CommandPalette
          open={paletteOpen}
          onClose={closePalette}
          items={paletteItems}
          title="命令面板"
        />
      </div>
    )
  }

  return (
    <div data-layout={layout} className="flex h-screen overflow-hidden text-ink">
      <Sidebar
        activeView={view}
        onSelect={(id) => {
          setView(id)
          setMobileNavOpen(false)
        }}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((c) => !c)}
        mobileOpen={mobileNavOpen}
        onCloseMobile={() => setMobileNavOpen(false)}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <TopStatusBar
          snap={snap}
          source={source}
          live={live}
          theme={theme}
          layout={layout}
          onCycleTheme={toggleTheme}
          onCycleLayout={toggleLayout}
          onOpenSearch={openPalette}
          onOpenMobileNav={() => setMobileNavOpen(true)}
        />
        <div className="flex-1 overflow-auto p-4">{mainContent}</div>
      </div>
      <CommandPalette
        open={paletteOpen}
        onClose={closePalette}
        items={paletteItems}
        title="命令面板"
      />
    </div>
  )
}

// local helper — token formatting for KPI (null -> UNKNOWN)
function fmtTokensSafe(tt: ReturnType<typeof tokenTruth>): string {
  if (!tt || tt.totalTokens == null) return 'UNKNOWN'
  const n = tt.totalTokens
  return n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : (n / 1e3).toFixed(0) + 'k'
}

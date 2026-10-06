import { useState, useEffect, useMemo, useCallback } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopStatusBar } from '@/components/layout/TopStatusBar'
import { CommandPalette, type PaletteItem } from '@/components/ui/command-palette'
import { Drawer } from '@/components/ui/drawer'
import { Toaster, useToaster } from '@/components/ui/toast'
import {
  MonitoringView, TrustView, SettingsView,
} from '@/views/Views'
import { CompactHUD } from '@/views/CompactHUD'
// L10 (2026-09-27): B10 overview landing surface (KPI grid + trends +
// Observer Map + system status + alerts + recent task packs).
import { OverviewView } from '@/views/OverviewView'
import {
  useLiveSnapshot,
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

// WORK-LAB-FRONTEND-TASKPACK-20260930: Control/Observer contract enforcement.
// Per taskpack authority: only Control Surface executes writes (through adapter/service contract); Observer projection never writes. All observer lanes (observer, rules-policy, audit, approvals as read-only projection) stay READ-ONLY; any approve/retry/cancel/rollback/install/apply must be blocked by backend contract and must not be reachable through hidden shortcuts/deep-links/shared components.
export default function App() {
  const [view, setView] = useState<ViewId>(readInitialView)
  const [theme, setTheme] = useState<ThemeMode>(readInitialTheme)
  const [layout, setLayout] = useState<LayoutMode>(readInitialLayout)
  // U06/SSE: live snapshot — first poll + server-sent events, no fixed ports.
  const { snap, source, live, error } = useLiveSnapshot()

  // UI_SHELL (20260921): mobile drawer + command palette.
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [paletteOpen, setPaletteOpen] = useState(false)
  // L10b: B10 global overlays — the right-hand 工作区 / Context drawer and the
  // bottom-right Toast (B10 `.drawer` + `.toast`, 1800ms auto-hide).
  const [workspaceOpen, setWorkspaceOpen] = useState(false)
  const { toasts, toast, dismiss } = useToaster(1800)

  const openPalette = useCallback(() => setPaletteOpen(true), [])
  const closePalette = useCallback(() => setPaletteOpen(false), [])

  // L6 keyboard authority: global Ctrl/Cmd+K toggles the command palette.
  // L10b: Esc closes every B10 overlay in one place (palette → modal handled
  // by the Modal itself → drawer), matching the B10 single-file keydown block.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setPaletteOpen((o) => !o)
      }
      if (e.key === 'Escape') {
        setPaletteOpen(false)
        setWorkspaceOpen(false)
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
        id: 'act-workspace',
        label: '打开工作区 / Context',
        group: '动作',
        run: () => setWorkspaceOpen(true),
      },
    ]
    return [...viewItems, ...actions]
  }, [theme, layout])

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
      <div className="panel mx-auto mt-10 max-w-xl text-center">
        <div className="mb-2 text-lg text-error">数据源不可用</div>
        <p className="whitespace-pre-wrap text-xs text-muted">{error}</p>
        <p className="mt-3 text-[11px] text-muted">
          保持 UNKNOWN 真相 — 不伪造 Agent / 模型 / 成本 / 资源
        </p>
      </div>
    ) : isOverview ? (
      <OverviewView snap={snap} source={source} live={live} />
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

  // L10b: the B10 global overlays (palette / workspace drawer / toast) render
  // in BOTH layouts so the Ctrl/Cmd+K contract, the honest toasts and the
  // read-only context drawer never depend on the shell variant.
  const overlays = (
    <>
      <CommandPalette
        open={paletteOpen}
        onClose={closePalette}
        items={paletteItems}
        title="命令面板"
      />
      <Drawer
        open={workspaceOpen}
        onClose={() => setWorkspaceOpen(false)}
        title="工作区 / Context"
      >
        <p className="m-0 text-sm text-muted">
          本地个人研究工作区：{snap ? 'Sidecar v3 快照投影已接入' : '数据源未接入（UNKNOWN）'}。
          Command Palette（Ctrl/Cmd + K）、Drawer、Toast 与 Modal 均可用；
          Observer 严格只读，无访问令牌 / 无锁定 / 无鉴权入口。
        </p>
        <div className="status-stack my-4">
          <span className="tag info">{live ? 'Live Transport' : (snap?.transport.transportState || 'UNKNOWN')}</span>
          <span className="tag ok">Local State</span>
          <span className="tag warn">Read-only</span>
        </div>
        <div className="panel">
          <h3>界面状态</h3>
          <div className="list">
            <div className="list-item"><span>Rendering</span><span className="tag ok">Ready</span></div>
            <div className="list-item"><span>Motion Effects</span><span className="tag ok">Enabled</span></div>
            <div className="list-item"><span>Palette</span><span className="tag info">Ctrl/Cmd + K</span></div>
            <div className="list-item"><span>Snapshot revision</span><span className="tag info">{snap ? String(snap.revision) : 'UNKNOWN'}</span></div>
          </div>
        </div>
      </Drawer>
      <Toaster toasts={toasts} onDismiss={dismiss} />
    </>
  )

  // U05: compact is a DEDICATED HUD — no sidebar, single column, 320px-safe.
  // full keeps the B10 sidebar + multi-panel layout.
  //
  // First-frame loading affordance. It sits ABOVE the lane content rather than
  // replacing it: the B5 rule pins that with no snapshot every KPI renders
  // UNKNOWN and never a fabricated 0, so swapping the content for a skeleton
  // would hide the very state the test defends. The strip answers "is it still
  // fetching?" without touching that discipline.
  const loadingStrip = (!snap && !error) ? (
    <div className="load-strip" role="status">
      投影加载中 · 首次快照未到达，数值保持 UNKNOWN，不预填任何数据
    </div>
  ) : null

  if (isCompact) {
    return (
      <div data-layout={layout} className="app app-compact">
        <div className="ambient" aria-hidden="true" />
        <div className="grid-bg" aria-hidden="true" />
        <main className="main">
          <TopStatusBar
            snap={snap}
            source={source}
            live={live}
            theme={theme}
            layout={layout}
            onCycleTheme={toggleTheme}
            onCycleLayout={toggleLayout}
            onOpenSearch={openPalette}
            onOpenDrawer={() => setWorkspaceOpen(true)}
            onNotify={() => toast({ title: '暂无新的通知', variant: 'info' })}
          />
          {loadingStrip}
          <section className="content" id="content">
            <CompactHUD snap={snap} live={live} />
          </section>
        </main>
        {overlays}
      </div>
    )
  }

  return (
    <div data-layout={layout} className="app">
      {/* L10 B10 `.ambient` + `.grid-bg`: the 32px grid backdrop (radial fade
          mask) + floating glow blobs — the "faint blue ambient light" the B10
          spec locks in (D-08: B10 beats the §八 "no glassmorphism flood"
          reading; the glow is the requested system state language). Both are
          the verbatim B10 elements: `.ambient` carries the `::before/::after`
          blobs, `.grid-bg` the grid. */}
      <div className="ambient" aria-hidden="true" />
      <div className="grid-bg" aria-hidden="true" />
      <Sidebar
        activeView={view}
        onSelect={(id) => {
          setView(id)
          setMobileNavOpen(false)
        }}
        mobileOpen={mobileNavOpen}
        onCloseMobile={() => setMobileNavOpen(false)}
      />
      <main className="main">
        <TopStatusBar
          snap={snap}
          source={source}
          live={live}
          theme={theme}
          layout={layout}
          onCycleTheme={toggleTheme}
          onCycleLayout={toggleLayout}
          onOpenSearch={openPalette}
          onOpenDrawer={() => setWorkspaceOpen(true)}
          onNotify={() => toast({ title: '暂无新的通知', variant: 'info' })}
          onOpenMobileNav={() => setMobileNavOpen(true)}
        />
        {loadingStrip}
        <section className="content" id="content">{mainContent}</section>
      </main>
      {overlays}
    </div>
  )
}

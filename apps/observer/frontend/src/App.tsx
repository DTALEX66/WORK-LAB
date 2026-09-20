import { useState, useEffect } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopStatusBar } from '@/components/layout/TopStatusBar'
import { KPICard } from '@/components/dashboard/KPICard'
import { ExecutionTable } from '@/components/dashboard/ExecutionTable'
import { ProjectPanel } from '@/components/dashboard/ProjectPanel'
import { TokenPanel } from '@/components/dashboard/TokenPanel'
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
    const l = new URLSearchParams(window.location.search).get('layout')
    if (l === 'full' || l === 'compact') return l
  } catch { /* ignore */ }
  return 'full'
}

export default function App() {
  const [view, setView] = useState<ViewId>(readInitialView)
  const [theme, setTheme] = useState<ThemeMode>(readInitialTheme)
  const [layout, setLayout] = useState<LayoutMode>(readInitialLayout)
  // U06/SSE: live snapshot — first poll + server-sent events, no fixed ports.
  const { snap, source, live, error } = useLiveSnapshot()

  // U05: real theme (dark/light) applied to <html> — no hardcoded class.
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

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
            value={String(snap?.projects?.length ?? 0)}
            sub="registry"
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
          />
          <div className="flex-1">
            <CompactHUD snap={snap} live={live} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div data-layout={layout} className="flex h-screen overflow-hidden text-ink">
      <Sidebar
        activeView={view}
        onSelect={(id) => setView(id)}
        collapsed={false}
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
        />
        <div className="flex-1 overflow-auto p-4">{mainContent}</div>
      </div>
    </div>
  )
}

// local helper — token formatting for KPI (null -> UNKNOWN)
function fmtTokensSafe(tt: ReturnType<typeof tokenTruth>): string {
  if (!tt || tt.totalTokens == null) return 'UNKNOWN'
  const n = tt.totalTokens
  return n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : (n / 1e3).toFixed(0) + 'k'
}

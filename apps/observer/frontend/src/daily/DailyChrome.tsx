// STITCH 交接包（references/main/*.png + DESIGN.md，2026-10-24）里日常壳的共享图元：
// 顶栏（logo 瓦片 / 居中搜索 + Ctrl+K 芯片 / HUD 按钮 / 无边框窗口控制）、左栏
// （WORKSPACE 标签 + 三项线性图标 + 底部设置与状态胶囊），以及卡片族图元。
// 复刻的是**布局与节奏**；槽位里出现的每个数都来自真实快照字段，缺字段就写 UNKNOWN，
// 需要执行动作的槽位保留视觉但禁用并写明被挡的效果（Observer 严格只读）。
import { ReactNode, useCallback, useEffect, useState } from 'react'
import {
  Boxes, ChevronDown, Clock, Command, FolderOpen, Lightbulb, Link2, Maximize2, Minimize2,
  Plug, Search, Settings, SquareArrowOutUpRight, Wrench, X,
} from 'lucide-react'
import { WindowControls } from '@/components/layout/WindowControls'

export const T = {
  bg: '#10141A', shell: '#171D25', surface: '#1C2430', text: '#E8EDF3',
  dim: '#A6B0BE', line: '#303A46', accent: '#40B6C7',
}

export type DailyNav = 'home' | 'issues' | 'tools'

const NAV_ICONS: Record<DailyNav, typeof FolderOpen> = {
  home: FolderOpen, issues: Lightbulb, tools: Wrench,
}

export function isNativeShell(): boolean {
  if (typeof window === 'undefined') return false
  try {
    if (new URLSearchParams(window.location.search).get('shell') === 'tauri') return true
  } catch { /* no URL */ }
  return '__TAURI_INTERNALS__' in window || '__TAURI__' in window
}

/** A rounded icon tile with the subject's own initials — derived from a real name, never a made-up glyph. */
export function IconTile({ label, size = 36, tone = 'shell' }: { label: string; size?: number; tone?: 'shell' | 'surface' }) {
  const initials = label.trim().slice(0, 2).toUpperCase()
  return (
    <span aria-hidden="true"
      className={`flex shrink-0 items-center justify-center rounded-lg border ${tone === 'shell' ? 'bg-[#1C2430]' : 'bg-[#171D25]'} font-semibold`}
      style={{ width: size, height: size, borderColor: T.line, color: T.accent, fontSize: Math.max(12, size * 0.34) }}>
      {initials}
    </span>
  )
}

const PILL_TONE: Record<string, string> = {
  正在推进: '#40B6C7', 需要关注: '#FBBF24', 等待你决定: '#FDE68A', 已完成: '#34D399', 暂停: '#A6B0BE',
}

/** The reference's "● 状态" capsule: dot + label inside a bordered pill. */
export function StatusPill({ status }: { status: string }) {
  const color = PILL_TONE[status] ?? T.dim
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs"
      style={{ borderColor: T.line, background: T.surface, color: T.text }}>
      <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
      {status}
    </span>
  )
}

export function Chip({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'accent' | 'warn' }) {
  const style = tone === 'accent'
    ? { borderColor: '#1F5F6B', background: 'rgba(64,182,199,0.12)', color: T.accent }
    : tone === 'warn'
      ? { borderColor: '#6B5320', background: 'rgba(251,191,36,0.10)', color: '#FCD34D' }
      : { borderColor: T.line, background: T.surface, color: T.dim }
  return (
    <span className="inline-flex items-center gap-1 whitespace-nowrap rounded border px-1.5 py-0.5 text-xs" style={style}>
      {children}
    </span>
  )
}

/** Section heading with the reference's accent left bar. */
export function SectionTitle({ children, right }: { children: ReactNode; right?: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <h2 className="flex items-center gap-2 text-sm font-semibold" style={{ color: T.text }}>
        <span aria-hidden="true" className="h-4 w-[3px] rounded-full" style={{ background: T.accent }} />
        {children}
      </h2>
      {right ? <span className="text-xs" style={{ color: T.dim }}>{right}</span> : null}
    </div>
  )
}

export function MetaItem({ icon, children }: { icon?: ReactNode; children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs" style={{ color: T.dim }}>
      {icon ?? null}{children}
    </span>
  )
}

export const TimeIcon = () => <Clock size={13} aria-hidden="true" />

/**
 * A slot the reference gives to an action the Observer must not take (launch a tool, register a
 * project). The visual stays so the layout is a true 1:1, but the control is disabled and names
 * the blocked effect instead of pretending to work.
 */
export function DisabledAction({ label, reason, primary = false }: { label: string; reason: string; primary?: boolean }) {
  return (
    <span className="inline-flex flex-col items-end gap-1">
      <button type="button" disabled aria-disabled="true" title={reason}
        className="inline-flex cursor-not-allowed items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm opacity-60"
        style={primary
          ? { borderColor: T.line, background: T.surface, color: T.dim }
          : { borderColor: T.line, background: T.shell, color: T.dim }}>
        {label}<SquareArrowOutUpRight size={13} aria-hidden="true" />
      </button>
      <span className="text-xs" style={{ color: T.dim }}>{reason}</span>
    </span>
  )
}

/** Toggle the native HUD strip. Under a browser entry there is no window to show, so it says so. */
function useHudToggle() {
  const native = isNativeShell()
  const [why, setWhy] = useState<string | null>(null)
  const toggle = useCallback(async () => {
    if (!native) { setWhy('浏览器入口没有原生窄窗；桌面主窗口或 HUD 窗口内可用') ; return }
    try {
      const { invoke } = await import('@tauri-apps/api/core')
      await invoke('show_hud')
      setWhy(null)
    } catch {
      setWhy('桌面壳未提供窄窗切换命令')
    }
  }, [native])
  return { native, why, toggle }
}

export function TopBar({ query, onQuery, hudHint }: {
  query: string; onQuery: (v: string) => void; hudHint: string | null
}) {
  const { toggle, why } = useHudToggle()
  useEffect(() => {
    if (!hudHint) return
    const onKey = (e: KeyboardEvent) => {
      if (e.altKey && (e.key === 'h' || e.key === 'H')) { e.preventDefault(); void toggle() }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [hudHint, toggle])
  const blocked = why ?? hudHint
  return (
    <header data-landmark="topbar" data-tauri-drag-region
      className="flex h-[52px] shrink-0 items-center gap-4 border-b px-4"
      style={{ borderColor: T.line, background: T.shell }}>
      <div className="flex items-center gap-2.5">
        <span aria-hidden="true" className="flex h-7 w-7 items-center justify-center rounded-md border"
          style={{ borderColor: T.line, background: T.surface, color: T.accent }}>
          <Boxes size={15} />
        </span>
        <span className="text-sm font-semibold tracking-wide" style={{ color: T.text }}>WORK-LAB</span>
      </div>
      <div className="relative mx-auto flex w-full max-w-[560px] items-center">
        <Search size={14} aria-hidden="true" className="pointer-events-none absolute left-3" style={{ color: T.dim }} />
        <input
          type="search" id="daily-global-search" value={query} onChange={(e) => onQuery(e.target.value)}
          aria-label="全局搜索" placeholder="快速导航或全局搜索…"
          className="h-8 w-full rounded-md border pl-9 pr-16 text-sm outline-none"
          style={{ borderColor: T.line, background: T.bg, color: T.text }}
        />
        <span className="pointer-events-none absolute right-3 inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-xs"
          style={{ borderColor: T.line, background: T.surface, color: T.dim }}>
          <Command size={11} aria-hidden="true" />K
        </span>
      </div>
      <div className="flex items-center gap-2">
        <button type="button" onClick={() => void toggle()} title={blocked ?? '显示／隐藏 HUD 窄窗'}
          className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs"
          style={{ borderColor: T.line, background: T.surface, color: T.text }}>
          <Plug size={13} aria-hidden="true" style={{ color: T.accent }} />
          HUD<span style={{ color: T.dim }}>Alt+H</span>
        </button>
      </div>
      <WindowControls />
    </header>
  )
}

export function Rail({ view, onNavigate, transportLabel, transportTone }: {
  view: DailyNav | 'settings'; onNavigate: (v: DailyNav | 'settings') => void
  transportLabel: string; transportTone: 'live' | 'unknown' | 'offline'
}) {
  const dot = transportTone === 'live' ? '#34D399' : transportTone === 'offline' ? '#FBBF24' : T.dim
  return (
    <nav aria-label="主导航" data-landmark="rail"
      className="flex w-[176px] shrink-0 flex-col border-r px-3 py-4"
      style={{ borderColor: T.line, background: T.shell }}>
      <div className="mb-3 px-2 text-xs uppercase tracking-wider" style={{ color: T.dim }}>工作区</div>
      <ul className="space-y-1">
        {(['home', 'issues', 'tools'] as DailyNav[]).map((id) => {
          const Icon = NAV_ICONS[id]
          const label = id === 'home' ? '项目' : id === 'issues' ? '问题与经验' : '我的工具'
          const active = view === id
          return (
            <li key={id}>
              <button type="button" onClick={() => onNavigate(id)} aria-current={active ? 'page' : undefined}
                className="relative flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm"
                style={active
                  ? { background: T.surface, color: T.accent }
                  : { color: T.dim }}>
                {active && (
                  <span aria-hidden="true" className="absolute left-0 top-1/2 h-5 w-[2px] -translate-y-1/2 rounded-full"
                    style={{ background: T.accent }} />
                )}
                <Icon size={15} aria-hidden="true" />
                {label}
              </button>
            </li>
          )
        })}
      </ul>
      <div className="mt-auto">
        <button type="button" onClick={() => onNavigate('settings')} aria-current={view === 'settings' ? 'page' : undefined}
          className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm"
          style={view === 'settings' ? { background: T.surface, color: T.accent } : { color: T.dim }}>
          <Settings size={15} aria-hidden="true" />设置
        </button>
        <div data-landmark="transport"
          className="mt-3 flex items-center justify-between gap-2 whitespace-nowrap rounded-md border px-2 py-1.5 text-xs"
          style={{ borderColor: T.line, background: T.bg, color: T.dim }}>
          <span className="inline-flex min-w-0 items-center gap-1.5 truncate">
            <span aria-hidden="true" className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: dot }} />
            {transportLabel}
          </span>
          <span className="shrink-0 uppercase tracking-wide">{transportTone === 'live' ? 'LIVE' : transportTone === 'offline' ? 'OFFLINE' : 'UNKNOWN'}</span>
        </div>
      </div>
    </nav>
  )
}

export { ChevronDown, Link2, Maximize2, Minimize2, X }

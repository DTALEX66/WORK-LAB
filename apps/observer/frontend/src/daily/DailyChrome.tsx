// STITCH 交接包（references/main/*.png + DESIGN.md，2026-10-24）里日常壳的共享图元：
// 顶栏（logo 瓦片 / 居中搜索 + Ctrl+K 芯片 / HUD 按钮 / 无边框窗口控制）、左栏
// （WORKSPACE 标签 + 三项线性图标 + 底部设置与状态胶囊），以及卡片族图元。
// 复刻的是**布局与节奏**；槽位里出现的每个数都来自真实快照字段，缺字段就写 UNKNOWN，
// 需要执行动作的槽位保留视觉但禁用并写明被挡的效果（Observer 严格只读）。
import { ReactNode, useCallback, useEffect, useState } from 'react'
import {
  ChevronDown, Clock, Command, FolderOpen, Lightbulb, Link2, Maximize2, Minimize2,
  Plug, Search, Settings, SquareArrowOutUpRight, Wrench, X,
} from 'lucide-react'
import { WindowControls } from '@/components/layout/WindowControls'

export const T = {
  bg: '#10141A', shell: '#171D25', surface: '#1C2430', text: '#E8EDF3',
  dim: '#A6B0BE', line: '#303A46', accent: '#40B6C7',
}

export type DailyNav = 'home' | 'issues' | 'tools'

// ── E1 · 主题诚实声明 ────────────────────────────────────────────────────
// 2026-10-25 实测：?theme=light 确实写进了 html.class（App.tsx 的主题效果与 index.html 预渲染
// 同一套契约），但日常壳与 HUD 窄窗三个文件里 var(--) 出现 0 次、十六进制值写死，
// 所以窄窗截图在两个主题下逐字节相同（md5 3f53ee67…）。令牌单源是 WUI-03 的后续项，浅色
// 配色还没接入本视图。owner 本轮的决定是「如实说明，不假装切换」：控件继续工作（专业投影壳
// 的主题切换是真的生效），但本表面必须把「这一屏暂时不跟着变」写在屏幕上。
// 措辞同时不许反向说谎：不得写成「本产品只有深色」。
export const THEME_HONESTY_ID_DAILY = 'daily-theme-honesty-note'
export const THEME_HONESTY_ID_HUD = 'hud-theme-honesty-note'

export const THEME_HONESTY_TEXT =
  '这一屏暂时不跟着变：这个按钮改的是页面的主题类与地址里的 ?theme=，而日常壳的配色按固定深色值写死，'
  + '还没接入主题令牌，所以它在这里只改地址参数 ?theme=，不会把本视图变成浅色。'
  + '要让它真的跟随主题，需要浅色板来源与令牌单源两样东西都到位（WUI-03），到位前这里不声称能切色。'
  + '专业投影壳（?view=…）的主题切换是实际生效的；把日常壳与 HUD 窄窗接进主题令牌是 WUI-03 的待办项。'

export const THEME_HONESTY_TEXT_HUD =
  '这个窄窗按固定的深色值绘制，?theme= 暂时不会改变它的配色；'
  + '专业投影壳的主题切换是实际生效的。接入主题令牌是 WUI-03 的待办项。'

/**
 * The honesty statement about the theme control, painted (never hover-only) and keyboard reachable
 * (tabIndex 0 + role=note) so it is not colour-only or tooltip-only information. The control it
 * describes points here with aria-describedby, and `title` repeats it for a pointer reader.
 * Same palette as the surrounding dim text, so both themes clear the floor by construction (the
 * surface paints identically): #A6B0BE on #10141A = 8.42:1, the #E8EDF3 lead-in on #10141A = 15.69:1,
 * both at text-xs = 12px — measured with the same WCAG formula `scripts/audit/text_legibility_via_cdp.py`
 * applies to painted text. No new size, no new colour pair.
 */
export function ThemeHonestyNote(props: { id: string; surface: 'daily' | 'hud' }) {
  const text = props.surface === 'hud' ? THEME_HONESTY_TEXT_HUD : THEME_HONESTY_TEXT
  return (
    <p id={props.id} role="note" tabIndex={0} title={text}
      data-testid="theme-honesty-note" data-theme-honesty="not-applied"
      data-surface={props.surface}
      className="mt-2 rounded border border-[#303A46] bg-[#10141A] p-2 text-xs leading-relaxed text-[#A6B0BE]">
      <span className="font-semibold text-[#E8EDF3]">主题未在本视图生效：</span>{text}
    </p>
  )
}

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
export function SectionTitle({ children, right, rightTone = 'text' }: {
  children: ReactNode; right?: ReactNode; rightTone?: 'text' | 'chip'
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
      <h2 className="flex shrink-0 items-center gap-2 text-sm font-semibold" style={{ color: T.text }}>
        <span aria-hidden="true" className="h-4 w-[3px] rounded-full" style={{ background: T.accent }} />
        {children}
      </h2>
      {right ? (rightTone === 'chip' ? (
        <span className="rounded-full border px-2 py-0.5 text-xs"
          style={{ borderColor: T.line, color: T.dim }}>{right}</span>
      ) : (
        <span className="min-w-0 text-right text-xs" style={{ color: T.dim }}>{right}</span>
      )) : null}
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
export function DisabledAction({ label, reason, primary = false, icon }: {
  label: string; reason: string; primary?: boolean; icon?: ReactNode
}) {
  return (
    <span className="inline-flex flex-col items-end gap-1">
      <button type="button" disabled aria-disabled="true" title={reason}
        className="inline-flex cursor-not-allowed items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm opacity-60"
        style={primary
          ? { borderColor: T.line, background: T.surface, color: T.dim }
          : { borderColor: T.line, background: T.shell, color: T.dim }}>
        {icon ?? null}{label}
        {icon ? null : <SquareArrowOutUpRight size={13} aria-hidden="true" />}
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
        <span aria-hidden="true" className="daily-brand-mark" data-brand-mark="work-lab" />
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
      <span aria-hidden="true" className="daily-rail-brand" data-brand-mark="work-lab" />
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

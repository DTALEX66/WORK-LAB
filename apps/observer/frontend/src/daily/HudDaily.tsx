// HUD 四态（H01 常驻窄面板 / H02 悬停摘要 / H03 单工具详情 / H04 外部回复提醒）。
// 一比一复刻 references/hud/H01..H04.png 的结构：notch 拖动把手、圆形额度槽位 + 右对齐数值列、
// 页脚状态点 + 齿轮。快照没有额度/余额/重置时间/用量序列：槽位保留，值一律 UNKNOWN，
// 环画成无进度，不画百分比、不画柱状图（DESIGN.md 与项目真值规则同时要求）。
// 原生窄窗宽 150px：展开态（H02/H03/H04）在窄窗里纵向堆叠在条体下方；440px 面板里按参考左右并排。
import { useMemo, useState } from 'react'
import type { SnapshotV3 } from '@/types'
import { fmtTimestamp } from '@/lib/api'
import { Settings, Sparkles } from 'lucide-react'

export type HudState = 'h01' | 'h02' | 'h03' | 'h04'

const LINE = '#303A46'
const ACCENT = '#40B6C7'

function ToolIcon({ label }: { label: string }) {
  return (
    <span aria-hidden="true"
      className="flex h-9 w-9 items-center justify-center rounded-full border text-xs"
      style={{ borderColor: LINE, background: '#1C2430', color: ACCENT }}>
      {label.slice(0, 2).toUpperCase()}
    </span>
  )
}

/**
 * The reference draws a progress ring per tool. The snapshot carries no quota field, so the ring is
 * rendered as a full, un-filled track: the slot exists, the value says UNKNOWN, and no arc implies a
 * percentage nobody measured.
 */
function RingSlot({ label }: { label: string }) {
  return (
    <span className="flex items-center justify-between gap-2">
      <span className="relative inline-flex h-9 w-9 items-center justify-center">
        <svg viewBox="0 0 36 36" width="36" height="36" aria-hidden="true">
          <circle cx="18" cy="18" r="15" fill="none" stroke={LINE} strokeWidth="3" />
        </svg>
        <span className="absolute text-xs" style={{ color: ACCENT }}>{label}</span>
      </span>
      <span className="text-xs" style={{ color: '#A6B0BE' }}>额度 UNKNOWN</span>
    </span>
  )
}

function readHs(): HudState {
  try {
    const s = new URLSearchParams(window.location.search).get('hs')
    if (s === 'h02' || s === 'h03' || s === 'h04') return s
  } catch { /* no URL */ }
  return 'h01'
}

function writeHs(state: HudState) {
  if (typeof window === 'undefined') return
  const p = new URLSearchParams(window.location.search)
  if (state === 'h01') p.delete('hs')
  else p.set('hs', state)
  const qs = p.toString()
  window.history.replaceState(null, '', window.location.pathname + (qs ? '?' + qs : ''))
}

export function HudDaily(props: { snap: SnapshotV3 | null; nativeStrip?: boolean }) {
  const { snap } = props
  const native = props.nativeStrip === true
  const [state, setState] = useState<HudState>(readHs)
  const [hoverSummary, setHoverSummary] = useState(false)
  const [miniSettings, setMiniSettings] = useState(false)
  const onState = (s: HudState) => { setState(s); writeHs(s) }
  const toolIds = useMemo(
    () => (snap?.adapterCapabilities ?? []).map((c) => ({ id: c.clientId, name: c.displayName || c.clientId })),
    [snap],
  )
  const waitingApprovals = (snap?.executions ?? [])
    .filter((e) => e.state === 'WAITING_APPROVAL' || e.state === 'WAITING_USER').length
  const activeProjects = (snap?.projects ?? []).filter((p) => p.activityState === 'ACTIVE').length
  const transport = snap?.transport
  // The strip is a summary surface: the reference keeps the footer pinned, so the row list is
  // capped and the remainder is stated instead of scrolling the footer out of the window.
  const MAX_STRIP_ROWS = 5
  const visibleTools = native ? toolIds.slice(0, MAX_STRIP_ROWS) : toolIds
  const hiddenToolCount = toolIds.length - visibleTools.length

  const h01Card = (
    <section aria-label="工具额度窄面板" data-landmark="h01"
      className="w-full max-w-[150px] rounded-2xl border bg-[#171D25] p-3"
      style={{ borderColor: LINE }}
      onMouseEnter={native ? () => setHoverSummary(true) : undefined}
      onMouseLeave={native ? () => setHoverSummary(false) : undefined}
      onFocus={native ? () => setHoverSummary(true) : undefined}
      onBlur={native ? () => setHoverSummary(false) : undefined}>
      <ul className="space-y-2.5">
        {toolIds.length === 0 && (
          <li className="py-2 text-center text-xs" style={{ color: '#A6B0BE' }}>未连接工具</li>
        )}
        {visibleTools.map((tool) => (
          <li key={tool.id}><RingSlot label={tool.name.slice(0, 2).toUpperCase()} /></li>
        ))}
        {hiddenToolCount > 0 && (
          // 条体高度有限：参考图也是"少数几行 + 常驻页脚"。溢出如实说明，不把页脚顶出视口。
          <li className="pt-1 text-center text-xs" style={{ color: '#A6B0BE' }}>
            另有 {hiddenToolCount} 个工具未在此列出（完整列表在主窗口）
          </li>
        )}
        {/* 余额行：快照没有余额字段，槽位在、值未知 */}
        <li className="border-t pt-2" style={{ borderColor: LINE }}>
          <span className="flex items-center justify-between gap-2">
            <span className="text-xs" style={{ color: '#A6B0BE' }}>余额</span>
            <span className="text-sm font-semibold" style={{ color: '#FBBF24' }}>UNKNOWN</span>
          </span>
        </li>
      </ul>
      <div className="mt-3 flex items-center justify-between border-t pt-2 text-xs" style={{ borderColor: LINE }}>
        <span style={{ color: '#A6B0BE' }}>项目 {activeProjects} · 待审 {waitingApprovals}</span>
        <button type="button" onClick={() => onState('h03')} style={{ color: ACCENT }}>详情</button>
      </div>
    </section>
  )

  const h02Section = (
    <section aria-label="悬停摘要" data-landmark="h02"
      className="w-full max-w-[300px] rounded-2xl border bg-[#171D25] p-3" style={{ borderColor: LINE }}>
      <h2 className="text-xs font-semibold">当前工具对应窗口</h2>
      {toolIds.length === 0
        ? <p className="mt-2 text-xs" style={{ color: '#A6B0BE' }}>未连接工具</p>
        : toolIds.slice(0, 3).map((tool) => (
          <div key={tool.id} className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs">
            <span>{tool.name}</span>
            <span style={{ color: '#A6B0BE' }}>窗口 待确认 · 数值 UNKNOWN · 重置时间 待确认</span>
          </div>
        ))}
      <p className="mt-3 text-xs" style={{ color: '#A6B0BE' }}>
        额度口径未提供（余额与额度分开显示，不做百分比）。
      </p>
      <div className="mt-2 flex gap-2">
        <button type="button" onClick={() => onState('h01')} className="text-xs" style={{ color: ACCENT }}>返回面板</button>
        <button type="button" onClick={() => onState('h03')} className="text-xs" style={{ color: ACCENT }}>
          工具详情（键盘等效入口）
        </button>
      </div>
    </section>
  )

  const h03Section = (
    <section aria-label="工具详情" data-landmark="h03"
      className="w-full max-w-[400px] rounded-2xl border bg-[#171D25] p-4" style={{ borderColor: LINE }}>
      <div className="flex items-center gap-3">
        <ToolIcon label={toolIds[0]?.name ?? '?'} />
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-semibold">{toolIds[0]?.name ?? '未连接工具'}</h2>
          <p className="text-xs" style={{ color: '#A6B0BE' }}>账户 UNKNOWN · 额度窗口 待确认</p>
        </div>
      </div>
      <dl className="mt-4 space-y-2 text-xs">
        <div className="flex justify-between gap-3"><dt>更新时间</dt>
          <dd className="text-right" style={{ color: '#A6B0BE' }}>
            {snap?.adapterCapabilities?.[0]?.observedAt ? fmtTimestamp(snap.adapterCapabilities[0].observedAt) : 'UNKNOWN'}
          </dd></div>
        <div className="flex justify-between gap-3"><dt>相关会话</dt>
          <dd style={{ color: '#A6B0BE' }}>{snap ? `${snap.executions.length} 条执行记录` : 'UNKNOWN'}</dd></div>
        <div className="flex justify-between gap-3"><dt>关联项目</dt>
          <dd className="text-right" style={{ color: '#A6B0BE' }}>
            {(snap?.projects ?? []).length ? (snap?.projects ?? []).map((p) => p.displayName ?? p.projectId).join('、') : '未记录'}
          </dd></div>
      </dl>
      {/* 参考在此画 Tokens 柱状图；快照没有用量序列，槽位保留并写明没有数据 */}
      <div className="mt-3 rounded-lg border p-3" style={{ borderColor: LINE, background: '#10141A' }}>
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold">Tokens</span>
          <span style={{ color: '#A6B0BE' }}>24h · UNKNOWN</span>
        </div>
        <p className="mt-1 text-xs" style={{ color: '#A6B0BE' }}>
          无用量序列数据：不绘制柱状图，不虚构数值。
        </p>
      </div>
      <div className="mt-3 flex gap-3">
        <button type="button" onClick={() => onState('h01')} className="text-xs" style={{ color: ACCENT }}>返回面板</button>
        <button type="button" onClick={() => onState('h04')} className="text-xs" style={{ color: ACCENT }}>提醒</button>
      </div>
    </section>
  )

  const h04Section = (
    <section aria-label="新回复提醒" data-landmark="h04"
      className="w-full max-w-[380px] rounded-2xl border bg-[#171D25] p-4" style={{ borderColor: LINE }}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="flex items-center gap-2 text-sm font-semibold">
            <Sparkles size={14} aria-hidden="true" style={{ color: '#FBBF24' }} />
            外部回复提醒
          </h2>
          <p className="mt-0.5 text-xs" style={{ color: '#A6B0BE' }}>
            工具：{toolIds[0]?.name ?? '未连接'} · 关联项目：{(snap?.projects ?? [])[0]?.displayName ?? '未记录'}
          </p>
        </div>
        <span className="flex items-center gap-2">
          <span className="rounded-full border px-2 py-0.5 text-xs" style={{ borderColor: LINE, color: ACCENT }}>新回复</span>
          <button type="button" onClick={() => onState('h01')} aria-label="关闭提醒" style={{ color: '#A6B0BE' }}>✕</button>
        </span>
      </div>
      <p className="mt-3 text-xs font-medium">启动与依赖排查脚本已就绪</p>
      <p className="mt-1 text-xs" style={{ color: '#A6B0BE' }}>
        当前数据源未提供外部回复事件，摘要保持 待确认；外部回复不等于系统确认，审批回到原工具处理。
      </p>
      <div className="mt-2 flex items-center justify-between text-xs" style={{ color: '#A6B0BE' }}>
        <span>时间：{snap ? fmtTimestamp(snap.sourceWatermark) : 'UNKNOWN'}</span>
        <span className="rounded border px-1.5 py-0.5" style={{ borderColor: LINE }}>
          项目: {(snap?.projects ?? [])[0]?.projectId ?? '未记录'}
        </span>
      </div>
      <div className="mt-3 flex gap-2">
        <button type="button" onClick={() => onState('h03')}
          className="rounded border px-2.5 py-1 text-xs" style={{ borderColor: LINE, color: '#A6B0BE' }}>
          查看相关用量
        </button>
        <button type="button" onClick={() => onState('h03')}
          className="flex-1 rounded bg-[#40B6C7] px-2.5 py-1 text-xs font-medium text-[#10141A]">
          返回外部工具查看 ↗
        </button>
      </div>
    </section>
  )

  const stateSwitcher = (
    <div className="flex flex-wrap justify-center gap-1 text-xs" aria-label="HUD 状态切换">
      {(['h01', 'h02', 'h03', 'h04'] as HudState[]).map((s) => (
        <button key={s} type="button" onClick={() => onState(s)}
          aria-pressed={state === s}
          className={`rounded px-2 py-1 ${state === s ? 'bg-[#1C2430] text-[#40B6C7]' : 'text-[#A6B0BE]'}`}>
          {s.toUpperCase()}
        </button>
      ))}
    </div>
  )

  const footer = native ? (
    <div data-landmark="hud-footer"
      className="mt-auto flex w-full items-center justify-between border-t pt-2 text-xs" style={{ borderColor: LINE }}>
      <span className="flex items-center gap-1.5" style={{ color: '#A6B0BE' }}>
        <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full"
          style={{ background: transport?.transportState === 'LIVE' ? '#34D399' : '#A6B0BE' }} />
        {transport?.transportState ?? 'UNKNOWN'}
      </span>
      <button type="button" aria-expanded={miniSettings} aria-label="HUD 设置"
        onClick={() => setMiniSettings((v) => !v)} style={{ color: '#A6B0BE' }}>
        <Settings size={14} aria-hidden="true" />
      </button>
    </div>
  ) : null

  return (
    <div className={`flex h-screen flex-col items-center gap-2 overflow-y-auto bg-[#10141A] p-2 text-[#E8EDF3] ${native ? 'justify-start' : 'justify-center gap-3'}`}
      data-hud-state={state} data-hud-frame={native ? 'native-strip' : 'panel'}>
      {native && (
        // 参考图顶部的 notch 把手：borderless 窄窗的拖动面（与 TopStatusBar 的 .drag-region 同一属性约定）。
        <div data-tauri-drag-region aria-hidden="true"
          className="mx-auto h-1.5 w-10 shrink-0 rounded-full" style={{ background: LINE }} />
      )}

      {native ? (
        <>
          {state === 'h01' && h01Card}
          {state === 'h01' && hoverSummary && h02Section}
          {state === 'h02' && h02Section}
          {state === 'h03' && h03Section}
          {state === 'h04' && h04Section}
          {miniSettings && (
            <div data-landmark="hud-settings"
              className="w-full rounded-xl border bg-[#171D25] p-2 text-xs" style={{ borderColor: LINE }}>
              <p style={{ color: '#A6B0BE' }}>
                数据源：{transport?.transportState ?? 'UNKNOWN'}；
                修订 {snap?.revision ?? 'UNKNOWN'}。
                主题与更多设置在主窗口设置页。
              </p>
              <button type="button" onClick={() => setMiniSettings(false)} className="mt-1" style={{ color: ACCENT }}>
                收起
              </button>
            </div>
          )}
          {footer}
        </>
      ) : (
        <>
          <div className="flex w-full items-start justify-center gap-3">
            {state === 'h01' && h01Card}
            {state === 'h02' && h02Section}
            {state === 'h03' && h03Section}
            {state === 'h04' && h04Section}
          </div>
          {stateSwitcher}
        </>
      )}
    </div>
  )
}

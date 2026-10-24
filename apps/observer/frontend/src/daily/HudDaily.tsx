// HUD 四态（H01 常驻窄面板 / H02 悬停摘要 / H03 工具详情 / H04 新回复提醒）。
// 默认工具视角。快照没有额度/余额数据：百分比一律 UNKNOWN、不补 0、不画虚构柱状图；
// DeepSeek 等余额类单独标注口径。原生窗口行为（贴边/拖动/多显示器/DPI）未在浏览器中验证。
import { useMemo, useState } from 'react'
import type { SnapshotV3 } from '@/types'
import { fmtTimestamp } from '@/lib/api'

export type HudState = 'h01' | 'h02' | 'h03' | 'h04'

const RING = 'border-[#303A46]'

function ToolIcon({ label }: { label: string }) {
  return (
    <span aria-hidden="true"
      className={`flex h-9 w-9 items-center justify-center rounded-full border ${RING} text-xs text-[#A6B0BE]`}>
      {label.slice(0, 2).toUpperCase()}
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

export function HudDaily(props: { snap: SnapshotV3 | null }) {
  const { snap } = props
  const [state, setState] = useState<HudState>(readHs)
  const onState = (s: HudState) => { setState(s); writeHs(s) }
  const toolIds = useMemo(
    () => (snap?.adapterCapabilities ?? []).map((c) => ({ id: c.clientId, name: c.displayName || c.clientId })),
    [snap],
  )
  const waitingApprovals = (snap?.executions ?? [])
    .filter((e) => e.state === 'WAITING_APPROVAL' || e.state === 'WAITING_USER').length
  const activeProjects = (snap?.projects ?? []).filter((p) => p.activityState === 'ACTIVE').length

  return (
    <div className="flex h-screen flex-col items-center justify-center gap-3 bg-[#10141A] p-4 text-[#E8EDF3]" data-hud-state={state}>
      {state === 'h01' && (
        <section aria-label="工具额度窄面板" className="w-[150px] rounded-2xl border border-[#303A46] bg-[#171D25] p-3">
          <ul className="space-y-2">
            {toolIds.length === 0 && (
              <li className="py-2 text-center text-xs text-[#A6B0BE]">未连接工具</li>
            )}
            {toolIds.map((tool) => (
              <li key={tool.id} className="flex items-center justify-between">
                <ToolIcon label={tool.name} />
                {/* v3 快照没有额度数据：未知保持未知，不用百分比圆环冒充 */}
                <span className="text-xs text-[#A6B0BE]">额度 UNKNOWN</span>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex items-center justify-between border-t border-[#303A46] pt-2 text-xs text-[#A6B0BE]">
            <span>项目 {activeProjects} · 待审 {waitingApprovals}</span>
            <button type="button" onClick={() => onState('h03')} className="text-[#40B6C7]">详情</button>
          </div>
        </section>
      )}

      {state === 'h02' && (
        <section aria-label="悬停摘要" className="w-[300px] rounded-2xl border border-[#303A46] bg-[#171D25] p-4">
          <h2 className="text-xs font-semibold">当前工具对应窗口</h2>
          {toolIds.length === 0
            ? <p className="mt-2 text-xs text-[#A6B0BE]">未连接工具</p>
            : toolIds.map((tool) => (
              <div key={tool.id} className="mt-2 flex items-center justify-between text-xs">
                <span>{tool.name}</span>
                <span className="text-[#A6B0BE]">窗口 待确认 · 数值 UNKNOWN · 重置时间 待确认</span>
              </div>
            ))}
          <p className="mt-3 text-xs text-[#A6B0BE]">额度口径未提供（余额与额度分开显示，不做百分比）。</p>
          <div className="mt-2 flex gap-2">
            <button type="button" onClick={() => onState('h01')} className="text-xs text-[#40B6C7]">返回面板</button>
            <button type="button" onClick={() => onState('h03')} className="text-xs text-[#40B6C7]">工具详情（键盘等效入口）</button>
          </div>
        </section>
      )}

      {state === 'h03' && (
        <section aria-label="工具详情" className="w-[400px] rounded-2xl border border-[#303A46] bg-[#171D25] p-5">
          <div className="flex items-center gap-3">
            <ToolIcon label={toolIds[0]?.name ?? '?'} />
            <div>
              <h2 className="text-sm font-semibold">{toolIds[0]?.name ?? '未连接工具'}</h2>
              <p className="text-xs text-[#A6B0BE]">账户 UNKNOWN · 额度窗口 待确认</p>
            </div>
          </div>
          <dl className="mt-4 space-y-2 text-xs">
            <div className="flex justify-between"><dt>更新时间</dt>
              <dd className="text-[#A6B0BE]">{snap?.adapterCapabilities?.[0]?.observedAt ? fmtTimestamp(snap.adapterCapabilities[0].observedAt) : 'UNKNOWN'}</dd></div>
            <div className="flex justify-between"><dt>相关会话</dt>
              <dd className="text-[#A6B0BE]">{snap ? `${snap.executions.length} 条执行记录` : 'UNKNOWN'}</dd></div>
            <div className="flex justify-between"><dt>关联项目</dt>
              <dd className="text-[#A6B0BE]">{(snap?.projects ?? []).length ? (snap?.projects ?? []).map((p) => p.displayName ?? p.projectId).join('、') : '未记录'}</dd></div>
          </dl>
          <p className="mt-3 text-xs text-[#A6B0BE]">无用量序列数据：不绘制柱状图，不虚构数值。</p>
          <div className="mt-3 flex gap-3">
            <button type="button" onClick={() => onState('h01')} className="text-xs text-[#40B6C7]">返回面板</button>
            <button type="button" onClick={() => onState('h04')} className="text-xs text-[#40B6C7]">提醒</button>
          </div>
        </section>
      )}

      {state === 'h04' && (
        <section aria-label="新回复提醒" className="w-[380px] rounded-2xl border border-[#303A46] bg-[#171D25] p-5">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-sm font-semibold">外部回复提醒</h2>
              <p className="text-xs text-[#A6B0BE]">工具：{toolIds[0]?.name ?? '未连接'} · 关联项目：{(snap?.projects ?? [])[0]?.displayName ?? '未记录'}</p>
            </div>
            <button type="button" onClick={() => onState('h01')} aria-label="关闭提醒" className="text-[#A6B0BE]">✕</button>
          </div>
          <p className="mt-3 text-xs text-[#A6B0BE]">
            当前数据源未提供外部回复事件，摘要保持 待确认；外部回复不等于系统确认，审批回到原工具处理。
          </p>
          <p className="mt-2 text-xs text-[#A6B0BE]">时间：{snap ? fmtTimestamp(snap.sourceWatermark) : 'UNKNOWN'}</p>
          <button type="button" onClick={() => onState('h03')}
            className="mt-4 w-full rounded bg-[#40B6C7] py-1.5 text-xs font-medium text-[#10141A]">
            查看相关用量
          </button>
        </section>
      )}

      <div className="flex gap-2 text-xs" aria-label="HUD 状态切换">
        {(['h01', 'h02', 'h03', 'h04'] as HudState[]).map((s) => (
          <button key={s} type="button" onClick={() => onState(s)}
            aria-pressed={state === s}
            className={`rounded px-2 py-1 ${state === s ? 'bg-[#1C2430] text-[#40B6C7]' : 'text-[#A6B0BE]'}`}>
            {s.toUpperCase()}
          </button>
        ))}
      </div>
    </div>
  )
}

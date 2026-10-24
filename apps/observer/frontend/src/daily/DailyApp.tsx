// 日常壳（2026-10-24 TRAE 交接包）：M01 项目首页 / M02 项目概览 / M03 问题与经验 /
// M04 方法交接抽屉 / M05 我的工具，一级导航 项目/问题与经验/我的工具，设置底置。
// 数据只来自真实快照、/api/v1/repair-packs 与 /api/v1/solutions；缺数据如实 UNKNOWN。
// 本壳经 ?shell=daily 进入，不替换专业投影壳；高级入口从这里链接过去。
import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import type { SnapshotV3 } from '@/types'
import { fmtTimestamp, repairPacksEndpoint } from '@/lib/api'
import {
  makeHttpRepairPackReader,
  writeClipboardText, type ManualRepairPack, type RepairPacksView,
} from '@/lib/repairPack'
import {
  fetchSolutions, type SolutionSearchView, type SolutionItem,
} from '@/daily/solutionsClient'
import { WindowControls } from '@/components/layout/WindowControls'
import {
  dailyProjectCards, dailyIssueRows, dailyToolRows, buildHandoverMaterial,
  type DailyProjectCard, type DailyIssueRow, type DailyToolRow,
} from '@/daily/dailyData'

export type DailyView = 'home' | 'overview' | 'issues' | 'tools' | 'settings'

const DAILY_PARAMS = ['shell', 'dv', 'dp', 'dq', 'dm', 'dtool'] as const

function readParams(): { dv: DailyView; dp: string | null; dq: string; dm: string | null; dtool: string | null } {
  try {
    const s = new URLSearchParams(window.location.search)
    const dvRaw = s.get('dv')
    const dv: DailyView = dvRaw === 'overview' || dvRaw === 'issues' || dvRaw === 'tools' || dvRaw === 'settings'
      ? dvRaw : 'home'
    return { dv, dp: s.get('dp'), dq: s.get('dq') ?? '', dm: s.get('dm'), dtool: s.get('dtool') }
  } catch {
    return { dv: 'home', dp: null, dq: '', dm: null, dtool: null }
  }
}

function writeParams(state: { dv: DailyView; dp: string | null; dq: string; dm: string | null; dtool: string | null }) {
  if (typeof window === 'undefined') return
  const p = new URLSearchParams(window.location.search)
  const setOrDrop = (name: string, value: string | null) => {
    if (value) p.set(name, value)
    else p.delete(name)
  }
  // 入口标记写回 `surface`，不改写 `shell`：桌面入口的 shell=tauri 是无边框壳的自声明，
  // 被任何一次导航覆盖掉，窗口控件就只能靠 IPC 注入探测来判定（浏览器里则应完全没有）。
  setOrDrop('surface', 'daily')
  setOrDrop('dv', state.dv === 'home' ? null : state.dv)
  setOrDrop('dp', state.dp)
  setOrDrop('dq', state.dq || null)
  setOrDrop('dm', state.dm)
  setOrDrop('dtool', state.dtool)
  const qs = p.toString()
  window.history.replaceState(null, '', window.location.pathname + (qs ? '?' + qs : ''))
}

const SURFACE = 'bg-[#1C2430] border border-[#303A46]'

function StatusDot({ status }: { status: string }) {
  const color = status === '正在推进' ? 'bg-[#40B6C7]'
    : status === '需要关注' ? 'bg-amber-400'
      : status === '等待你决定' ? 'bg-yellow-300'
        : status === '已完成' ? 'bg-emerald-400'
          : status === '暂停' ? 'bg-[#A6B0BE]' : 'bg-[#A6B0BE]'
  return <span aria-hidden="true" className={`inline-block h-2 w-2 rounded-full ${color}`} />
}

export function DailyApp(props: {
  snap: SnapshotV3 | null
  live: boolean
  error: string | null
  theme: string
  onTheme: (t: 'dark' | 'light') => void
}) {
  const { snap, live, error } = props
  const [state, setState] = useState(readParams)
  const [packsView, setPacksView] = useState<RepairPacksView | null>(null)
  const [packsState, setPacksState] = useState<'LOADING' | 'OK' | 'UNREACHABLE' | 'BAD'>('LOADING')
  const [packsWhy, setPacksWhy] = useState<string | null>(null)
  const [solutions, setSolutions] = useState<SolutionSearchView | null>(null)
  const [solutionsState, setSolutionsState] = useState<'LOADING' | 'OK' | 'UNREACHABLE' | 'BAD'>('LOADING')
  const [solutionsWhy, setSolutionsWhy] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<Record<string, { verdict: string; note: string }>>({})
  const [copyState, setCopyState] = useState<Record<string, { ok: boolean; why?: string }>>({})
  const searchRef = useRef<HTMLInputElement>(null)

  const navigate = useCallback((patch: Partial<typeof state>) => {
    setState((prev) => {
      const next = { ...prev, ...patch }
      writeParams(next)
      return next
    })
  }, [])

  // 返回键保留上下文：查询与筛选都活在 URL 里，这里只负责前进动作。
  const openProject = (projectId: string) => navigate({ dv: 'overview', dp: projectId })
  const backHome = () => navigate({ dv: 'home', dp: null })
  const openMethod = (solutionId: string) => navigate({ dm: solutionId })
  const closeMethod = () => navigate({ dm: null })

  useEffect(() => {
    const endpoint = repairPacksEndpoint()
    if (!endpoint) { setPacksState('UNREACHABLE'); setPacksWhy('没有可信任的 loopback 端点'); return }
    const reader = makeHttpRepairPackReader(endpoint.url)
    const controller = new AbortController()
    reader(controller.signal).then((outcome) => {
      if (controller.signal.aborted) return
      if (outcome.kind === 'RESULT') { setPacksView(outcome.view); setPacksState('OK') }
      else if (outcome.kind === 'UNREACHABLE') { setPacksState('UNREACHABLE'); setPacksWhy(outcome.detail) }
      else { setPacksState('BAD'); setPacksWhy(outcome.why) }
    }).catch(() => { if (!controller.signal.aborted) setPacksState('UNREACHABLE') })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    setSolutionsState('LOADING')
    fetchSolutions(state.dq, controller.signal).then((outcome) => {
      if (controller.signal.aborted) return
      if (outcome.kind === 'RESULT') { setSolutions(outcome.view); setSolutionsState('OK') }
      else if (outcome.kind === 'UNREACHABLE') { setSolutionsState('UNREACHABLE'); setSolutionsWhy(outcome.detail) }
      else { setSolutionsState('BAD'); setSolutionsWhy(outcome.why) }
    }).catch(() => { if (!controller.signal.aborted) setSolutionsState('UNREACHABLE') })
    return () => controller.abort()
  }, [state.dq])

  const cards = useMemo(() => dailyProjectCards(snap, packsView?.packs ?? []), [snap, packsView])
  const issues = useMemo(() => dailyIssueRows(snap, packsView?.packs ?? []), [snap, packsView])
  const tools = useMemo(() => dailyToolRows(snap), [snap])

  const filteredProjects = useMemo(() => {
    const q = state.dq.trim().toLowerCase()
    if (!q) return cards
    return cards.filter((c) => c.displayName.toLowerCase().includes(q) || c.projectId.toLowerCase().includes(q))
  }, [cards, state.dq])

  const filteredIssues = useMemo(() => {
    const q = state.dq.trim().toLowerCase()
    if (!q) return issues
    return issues.filter((i) => i.title.toLowerCase().includes(q) || i.classLabel.toLowerCase().includes(q)
      || (i.projectId ?? '').toLowerCase().includes(q))
  }, [issues, state.dq])

  const filteredTools = useMemo(() => {
    const q = state.dq.trim().toLowerCase()
    if (!q) return tools
    return tools.filter((t) => t.displayName.toLowerCase().includes(q) || t.clientId.toLowerCase().includes(q))
  }, [tools, state.dq])

  const selectedProject = useMemo(
    () => (snap?.projects ?? []).find((p) => p.projectId === state.dp) ?? null,
    [snap, state.dp],
  )
  const selectedCard = cards.find((c) => c.projectId === state.dp) ?? null
  const projectIssues = issues.filter((i) => i.projectId === state.dp)
  const selectedMethod: SolutionItem | null = useMemo(
    () => solutions?.results.find((r) => r.solutionId === state.dm) ?? null,
    [solutions, state.dm],
  )
  const selectedTool = tools.find((t) => t.clientId === state.dtool) ?? tools[0] ?? null

  const searchDisabledNote = error && !snap ? '数据源不可用，显示 OFFLINE，不加载演示数据' : null

  // —— 全局快捷键：Ctrl/Cmd+K 聚焦搜索（快捷键不是搜索功能本身）——
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        searchRef.current?.focus()
        searchRef.current?.select()
      }
      if (e.key === 'Escape') closeMethod()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const navItems: { id: DailyView; label: string }[] = [
    { id: 'home', label: '项目' },
    { id: 'issues', label: '问题与经验' },
    { id: 'tools', label: '我的工具' },
  ]

  const shell = (
    <div className="flex h-screen flex-col bg-[#10141A] text-[#E8EDF3]" data-shell="daily">
      <div className="flex min-h-0 flex-1">
        {/* 左侧窄栏：三个一级入口 + 设置底置 */}
        <nav aria-label="主导航" className="flex w-[176px] shrink-0 flex-col border-r border-[#303A46] bg-[#171D25] px-3 py-4">
          <div className="mb-6 px-2 text-sm font-semibold tracking-wide">WORK-LAB</div>
          <div className="text-xs uppercase tracking-wider text-[#A6B0BE]">工作区</div>
          <ul className="mt-2 space-y-1">
            {navItems.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => navigate({ dv: item.id, dp: item.id === 'home' ? null : state.dp })}
                  aria-current={state.dv === item.id ? 'page' : undefined}
                  className={`w-full rounded px-3 py-2 text-left text-sm ${state.dv === item.id
                    ? 'bg-[#1C2430] text-[#40B6C7]' : 'text-[#A6B0BE] hover:text-[#E8EDF3]'}`}
                >
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
          <div className="mt-auto">
            <button
              type="button"
              onClick={() => navigate({ dv: 'settings' })}
              aria-current={state.dv === 'settings' ? 'page' : undefined}
              className={`w-full rounded px-3 py-2 text-left text-sm ${state.dv === 'settings'
                ? 'bg-[#1C2430] text-[#40B6C7]' : 'text-[#A6B0BE] hover:text-[#E8EDF3]'}`}
            >
              设置
            </button>
            <div className="mt-2 px-3 text-xs text-[#A6B0BE]">
              数据源：{error && !snap ? 'OFFLINE' : live ? 'LIVE' : snap ? 'UNVERIFIED' : 'UNKNOWN'}
            </div>
          </div>
        </nav>

        {/* 主区：顶栏（全局搜索）+ 内容。borderless 主窗口默认从这里进入，
            顶栏容器是拖动区（Tauri 注入 data-tauri-drag-region 处理），
            搜索框等交互元素不带该属性，点击行为不受影响。 */}
        <div className="flex min-h-0 flex-1 flex-col">
          <div data-tauri-drag-region className="flex items-center gap-3 border-b border-[#303A46] bg-[#171D25] px-5 py-3">
            <input
              ref={searchRef}
              type="search"
              value={state.dq}
              onChange={(e) => navigate({ dq: e.target.value })}
              placeholder="搜索项目、问题、工具与方法…"
              aria-label="全局搜索"
              className="min-w-0 flex-1 rounded border border-[#303A46] bg-[#10141A] px-3 py-1.5 text-sm outline-none focus:border-[#40B6C7]"
            />
            <span className="daily-kbd-hint text-xs text-[#A6B0BE]">Ctrl+K</span>
          </div>
          {searchDisabledNote && (
            <div role="alert" className="border-b border-[#303A46] bg-[#171D25] px-5 py-2 text-xs text-amber-300">
              {searchDisabledNote}
            </div>
          )}
          <main className="min-h-0 flex-1 overflow-y-auto px-6 py-5" id="daily-content">
            {state.dv === 'home' && (
              <HomeView cards={filteredProjects} totalCount={cards.length} onOpen={openProject} />
            )}
            {state.dv === 'overview' && (
              <OverviewView
                card={selectedCard}
                issues={projectIssues}
                solutions={solutions}
                onBack={backHome}
                onOpenMethod={openMethod}
              />
            )}
            {state.dv === 'issues' && (
              <IssuesView
                rows={filteredIssues}
                totalCount={issues.length}
                issuesSummary={snap?.issuesSummary}
                onOpenMethod={openMethod}
                onOpenProject={(id) => openProject(id)}
                feedback={feedback}
                onFeedback={(fp, verdict) => setFeedback((prev) => ({
                  ...prev, [fp]: { verdict, note: prev[fp]?.note ?? '' },
                }))}
                onFeedbackNote={(fp, note) => setFeedback((prev) => ({
                  ...prev, [fp]: { verdict: prev[fp]?.verdict ?? '', note },
                }))}
              />
            )}
            {state.dv === 'tools' && (
              <ToolsView tools={filteredTools} selected={selectedTool} onSelect={(id) => navigate({ dtool: id })} />
            )}
            {state.dv === 'settings' && (
              <SettingsView theme={props.theme} onTheme={props.onTheme} snap={snap} />
            )}
            {state.dv !== 'settings' && state.dv !== 'home' && (
              <p className="mt-6 text-xs text-[#A6B0BE]">
                {snap ? `快照修订 ${snap.revision} · 采样 ${fmtTimestamp(snap.sourceWatermark)}` : '快照未到达 · 数值保持 UNKNOWN'}
              </p>
            )}
          </main>
        </div>
      </div>

      {state.dm && (
        <MethodDrawer
          method={selectedMethod}
          solutionsState={solutionsState}
          solutionsWhy={solutionsWhy}
          projectName={selectedCard?.displayName ?? state.dp}
          issues={issues}
          packs={packsView?.packs ?? []}
          tools={tools}
          onClose={closeMethod}
        />
      )}
    </div>
  )
  void copyState
  void DAILY_PARAMS
  // WindowControls portals to <body>; under a browser entry it renders null.
  // The desktop main window is borderless (decorations:false), so without this
  // cluster the default daily entry can neither minimize nor close from inside.
  return (
    <>
      {shell}
      <WindowControls />
    </>
  )
}

function HomeView(props: { cards: DailyProjectCard[]; totalCount: number; onOpen: (id: string) => void }) {
  return (
    <section aria-label="项目首页">
      <div className="mb-4 flex items-baseline gap-3">
        <h1 className="text-xl font-semibold">项目</h1>
        <span className="text-xs text-[#A6B0BE]">{props.totalCount} 个已注册项目</span>
      </div>
      {props.cards.length === 0 ? (
        <div className={`${SURFACE} rounded-lg p-6 text-sm text-[#A6B0BE]`}>
          {props.totalCount === 0
            ? '快照中没有已注册项目（实测为 0，不是缺字段）。'
            : '没有匹配当前搜索的项目。清除搜索词可恢复完整列表。'}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {props.cards.map((card) => (
            <article key={card.projectId} className={`${SURFACE} flex flex-col rounded-lg p-4`}>
              <div className="flex items-start justify-between gap-2">
                <h2 className="text-base font-semibold">{card.displayName}</h2>
                <span className="flex items-center gap-1.5 text-xs text-[#A6B0BE]">
                  <StatusDot status={card.status} />{card.status}
                </span>
              </div>
              <p className="mt-2 text-xs text-[#A6B0BE]">
                最近变化：{card.latestChange ? fmtTimestamp(card.latestChange) : '待确认'}
              </p>
              {card.attentionNote && <p className="mt-2 text-xs text-amber-300">{card.attentionNote}</p>}
              <p className="mt-2 text-xs text-[#A6B0BE]">
                关联工具：{card.relatedTools.length ? card.relatedTools.join('、') : '未记录'}
                {card.openIssueCount !== null && card.openIssueCount > 0 ? ` · ${card.openIssueCount} 个当前问题` : ''}
              </p>
              <div className="mt-4 flex items-center justify-between border-t border-[#303A46] pt-3">
                <span className="text-xs text-[#A6B0BE]">更新：{card.updatedAt ? fmtTimestamp(card.updatedAt) : 'UNKNOWN'}</span>
                <button type="button" onClick={() => props.onOpen(card.projectId)}
                  className="text-sm text-[#40B6C7] hover:underline">
                  进入项目概览 →
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

function OverviewView(props: {
  card: DailyProjectCard | null
  issues: DailyIssueRow[]
  solutions: SolutionSearchView | null
  onBack: () => void
  onOpenMethod: (id: string) => void
}) {
  const [techOpen, setTechOpen] = useState(false)
  if (!props.card) {
    return (
      <section aria-label="项目概览">
        <button type="button" onClick={props.onBack} className="text-sm text-[#40B6C7] hover:underline">← 所有项目</button>
        <div className={`${SURFACE} mt-4 rounded-lg p-6 text-sm text-[#A6B0BE]`}>
          链接指向的项目在本机投影中不存在（不猜测最近的项目）。
        </div>
      </section>
    )
  }
  return (
    <section aria-label="项目概览">
      <button type="button" onClick={props.onBack} className="text-sm text-[#40B6C7] hover:underline">← 所有项目</button>
      <header className={`${SURFACE} mt-3 rounded-lg p-5`}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="flex items-center gap-3 text-xl font-semibold">
              {props.card.displayName}
              <span className="flex items-center gap-1.5 text-xs font-normal text-[#A6B0BE]">
                <StatusDot status={props.card.status} />{props.card.status}
              </span>
            </h1>
            <p className="mt-2 text-sm text-[#A6B0BE]">
              最近变化：{props.card.latestChange ? fmtTimestamp(props.card.latestChange) : '待确认'}
              {' · '}关联工具：{props.card.relatedTools.length ? props.card.relatedTools.join('、') : '未记录'}
            </p>
          </div>
        </div>
      </header>
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className={`${SURFACE} rounded-lg p-5 ${props.issues.length ? 'border-t-2 border-t-amber-400' : ''}`}>
          <h2 className="text-sm font-semibold">需要关注的事项</h2>
          {props.issues.length === 0 ? (
            <p className="mt-2 text-xs text-[#A6B0BE]">本项目当前没有打开的问题（实测，非推断）。</p>
          ) : (
            <ul className="mt-3 space-y-3">
              {props.issues.map((issue) => (
                <li key={issue.fingerprint} className="rounded border border-[#303A46] bg-[#10141A] p-3">
                  <div className="text-sm font-medium">{issue.title}</div>
                  <p className="mt-1 text-xs text-[#A6B0BE]">{issue.classLabel} · {issue.priority} · 最近 {fmtTimestamp(issue.lastSeenAt)}</p>
                  {issue.hasPack
                    ? <p className="mt-1 text-xs text-[#40B6C7]">已有修复包草稿（未发送），在问题与经验页处理。</p>
                    : <p className="mt-1 text-xs text-[#A6B0BE]">尚无修复包；可在问题与经验页查看可参考方法。</p>}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className={`${SURFACE} rounded-lg p-5`}>
          <h2 className="text-sm font-semibold">可参考的历史经验</h2>
          {!props.solutions ? (
            <p className="mt-2 text-xs text-[#A6B0BE]">方案库状态：读取中（不预填结果）。</p>
          ) : props.solutions.status === 'SOURCE_ABSENT' ? (
            <p className="mt-2 text-xs text-[#A6B0BE]">方案库暂无法获取：{props.solutions.reason}</p>
          ) : props.solutions.results.length === 0 ? (
            <p className="mt-2 text-xs text-[#A6B0BE]">{props.solutions.reason}</p>
          ) : (
            <ul className="mt-3 space-y-3">
              {props.solutions.results.slice(0, 3).map((m) => (
                <li key={m.solutionId} className="rounded border border-[#303A46] bg-[#10141A] p-3">
                  <div className="text-sm font-medium">{m.title ?? m.solutionId}</div>
                  <p className="mt-1 text-xs text-[#A6B0BE]">
                    来源软件：{String(m.software.softwareId ?? '未记录')} · {m.versionHint?.message ?? '适用性待确认'}
                  </p>
                  <button type="button" onClick={() => props.onOpenMethod(m.solutionId)}
                    className="mt-2 text-xs text-[#40B6C7] hover:underline">
                    查看该方法详情 →
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      <div className={`${SURFACE} mt-4 rounded-lg`}>
        <button type="button" onClick={() => setTechOpen((o) => !o)} aria-expanded={techOpen}
          className="flex w-full items-center justify-between px-5 py-3 text-left text-sm">
          技术依据（默认折叠）
          <span aria-hidden="true">{techOpen ? '收起' : '展开'}</span>
        </button>
        {techOpen && (
          <dl className="grid grid-cols-2 gap-2 px-5 pb-4 text-xs text-[#A6B0BE]">
            <dt>活动状态</dt><dd>{props.card.status}</dd>
            <dt>最近强证据</dt><dd>{fmtTimestamp(props.card.latestChange)}</dd>
          </dl>
        )}
      </div>
    </section>
  )
}

function IssuesView(props: {
  rows: DailyIssueRow[]
  totalCount: number
  issuesSummary: SnapshotV3['issuesSummary']
  onOpenMethod: (id: string) => void
  onOpenProject: (id: string) => void
  feedback: Record<string, { verdict: string; note: string }>
  onFeedback: (fingerprint: string, verdict: string) => void
  onFeedbackNote: (fingerprint: string, note: string) => void
}) {
  const [expanded, setExpanded] = useState<string | null>(null)
  const summary = props.issuesSummary
  return (
    <section aria-label="问题与经验">
      <h1 className="text-xl font-semibold">问题与经验</h1>
      <p className="mt-1 text-xs text-[#A6B0BE]">
        正在影响软件项目的问题，以及可参考的过往解法。相似表现不等于相同根因。
      </p>
      {summary && (
        <p className="mt-2 text-xs text-[#A6B0BE]">
          来源 {summary.sourcesRead} 个 · 扫描 {summary.rowsScanned} 行 · 产出 {summary.emittedCount} 条
          {summary.truncated ? ' · 已截断' : summary.complete === false ? ' · 覆盖不完整' : ''}
        </p>
      )}
      <ul className="mt-4 space-y-3">
        {props.rows.length === 0 && (
          <li className={`${SURFACE} rounded-lg p-6 text-sm text-[#A6B0BE]`}>
            {props.totalCount === 0
              ? '当前没有打开的问题（实测，非推断）。'
              : '没有匹配当前搜索的问题。'}
          </li>
        )}
        {props.rows.map((issue) => {
          const open = expanded === issue.fingerprint
          return (
            <li key={issue.fingerprint} className={`${SURFACE} rounded-lg border-l-4 border-l-amber-400 p-4`}>
              <div className="flex items-start justify-between gap-3">
                <button type="button" onClick={() => setExpanded(open ? null : issue.fingerprint)}
                  aria-expanded={open} className="min-w-0 flex-1 text-left">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded bg-amber-400/15 px-2 py-0.5 text-xs text-amber-300">当前需要处理</span>
                    {issue.projectId && (
                      <button type="button" onClick={(e) => { e.stopPropagation(); props.onOpenProject(issue.projectId as string) }}
                        className="text-xs text-[#40B6C7] hover:underline">
                        {issue.projectId}
                      </button>
                    )}
                    <span className="text-xs text-[#A6B0BE]">{issue.priority} · {fmtTimestamp(issue.lastSeenAt)}</span>
                  </div>
                  <h2 className="mt-1 text-sm font-medium">{issue.title}</h2>
                  {issue.detail && <p className="mt-1 text-xs text-[#A6B0BE]">{issue.detail}</p>}
                </button>
              </div>
              {open && (
                <div className="mt-3 border-t border-[#303A46] pt-3">
                  <div className="text-xs text-[#A6B0BE]">
                    证据位置：{issue.fingerprint.slice(0, 24)}…（同类表现未必同因）
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                    <span>处理反馈：</span>
                    {['已恢复', '仍有问题', '不确定'].map((v) => (
                      <button key={v} type="button"
                        onClick={() => props.onFeedback(issue.fingerprint, v)}
                        className={`rounded border px-2 py-1 ${props.feedback[issue.fingerprint]?.verdict === v
                          ? 'border-[#40B6C7] text-[#40B6C7]' : 'border-[#303A46] text-[#A6B0BE]'}`}>
                        {v}
                      </button>
                    ))}
                    {props.feedback[issue.fingerprint]?.verdict && (
                      <span className="text-[#40B6C7]">你反馈：{props.feedback[issue.fingerprint].verdict}</span>
                    )}
                  </div>
                  {props.feedback[issue.fingerprint]?.verdict && (
                    <>
                      <input type="text" value={props.feedback[issue.fingerprint].note} placeholder="可附短说明（可选）"
                        onChange={(e) => props.onFeedbackNote(issue.fingerprint, e.target.value)}
                        className="mt-2 w-full rounded border border-[#303A46] bg-[#10141A] px-2 py-1 text-xs" />
                      <p className="mt-1 text-xs text-amber-300">
                        当前侧车没有写入接口（Observer 只读），反馈仅保存在本页内存中，刷新后丢失。
                      </p>
                    </>
                  )}
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}

function ToolsView(props: { tools: DailyToolRow[]; selected: DailyToolRow | null; onSelect: (id: string) => void }) {
  return (
    <section aria-label="我的工具">
      <h1 className="text-xl font-semibold">我的工具</h1>
      <p className="mt-1 text-xs text-[#A6B0BE]">管理外部 AI 与本地开发工具的连接身份与使用辅助。</p>
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        <ul className="space-y-2" aria-label="工具列表">
          {props.tools.length === 0 && (
            <li className={`${SURFACE} rounded-lg p-4 text-xs text-[#A6B0BE]`}>
              快照未携带适配器能力卡（来源缺失，不是 0 个工具）。
            </li>
          )}
          {props.tools.map((tool) => (
            <li key={tool.clientId}>
              <button type="button" onClick={() => props.onSelect(tool.clientId)}
                aria-current={props.selected?.clientId === tool.clientId ? 'true' : undefined}
                className={`w-full rounded-lg border p-3 text-left ${props.selected?.clientId === tool.clientId
                  ? 'border-[#40B6C7] bg-[#1C2430]' : 'border-[#303A46] bg-[#171D25]'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{tool.displayName}</span>
                  <span className="text-xs text-[#A6B0BE]">{tool.connection.includes('失败') || tool.connection.includes('未连接') ? '未连接' : '已连接'}</span>
                </div>
                <p className="mt-1 text-xs text-[#A6B0BE]">{tool.version ?? '版本 UNKNOWN'}</p>
              </button>
            </li>
          ))}
        </ul>
        <div className={`${SURFACE} rounded-lg p-5`}>
          {!props.selected ? (
            <p className="text-sm text-[#A6B0BE]">左侧选择一个工具查看详情。</p>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">{props.selected.displayName}</h2>
                <span className="text-xs text-[#A6B0BE]">{props.selected.connection}</span>
              </div>
              <dl className="mt-4 space-y-3 text-sm">
                <div className="rounded border border-[#303A46] bg-[#10141A] p-3">
                  <dt className="text-xs text-[#A6B0BE]">当前可用能力</dt>
                  <dd className="mt-1">{props.selected.capabilitySentence}</dd>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded border border-[#303A46] bg-[#10141A] p-3">
                    <dt className="text-xs text-[#A6B0BE]">关联项目</dt>
                    <dd className="mt-1">{props.selected.relatedProjects.length ? props.selected.relatedProjects.join('、') : '未记录'}</dd>
                  </div>
                  <div className="rounded border border-[#303A46] bg-[#10141A] p-3">
                    <dt className="text-xs text-[#A6B0BE]">声明版本</dt>
                    <dd className="mt-1">{props.selected.version ?? 'UNKNOWN'}</dd>
                  </div>
                  <div className="rounded border border-[#303A46] bg-[#10141A] p-3">
                    <dt className="text-xs text-[#A6B0BE]">写入策略</dt>
                    <dd className="mt-1">{props.selected.writePolicy || 'UNKNOWN'}</dd>
                  </div>
                </div>
              </dl>
              <div className="mt-5">
                <h3 className="text-sm font-semibold">使用辅助</h3>
                <ul className="mt-2 space-y-2 text-sm">
                  <li className="rounded border border-[#303A46] bg-[#10141A] px-3 py-2">使用方法 · 查看向该工具提供上下文与排错的建议做法</li>
                  <li className="rounded border border-[#303A46] bg-[#10141A] px-3 py-2">提示词与规则 · 查看现有交付格式模板与摘要约束</li>
                  <li className="rounded border border-[#303A46] bg-[#10141A] px-3 py-2">常见问题 · 查看连接中断或排查超时的常见处理问答</li>
                </ul>
              </div>
              <p className="mt-4 text-xs text-[#A6B0BE]">
                连接配置、专业接口与诊断在「设置 → 高级与专业视图」；本页不修改对方全局配置。
              </p>
            </>
          )}
        </div>
      </div>
    </section>
  )
}

function SettingsView(props: { theme: string; onTheme: (t: 'dark' | 'light') => void; snap: SnapshotV3 | null }) {
  const advanced = [
    { id: 'work', label: '工作' }, { id: 'projects', label: '项目（完整投影）' },
    { id: 'software', label: '软件' }, { id: 'capabilities', label: '能力资产' },
    { id: 'usage', label: '用量缓存' }, { id: 'environment', label: '软件环境' },
    { id: 'rules-policy', label: '规则策略' }, { id: 'audit', label: '审计追踪' },
    { id: 'approvals', label: '审批中心' }, { id: 'integrations', label: '集成/MCP' },
    { id: 'evidence', label: '证据区间' }, { id: 'settings', label: '专业设置' },
  ]
  return (
    <section aria-label="设置">
      <h1 className="text-xl font-semibold">设置</h1>
      <div className={`${SURFACE} mt-4 rounded-lg p-5`}>
        <h2 className="text-sm font-semibold">外观</h2>
        <div className="mt-3 flex items-center gap-3 text-sm">
          <span>主题</span>
          <button type="button" onClick={() => props.onTheme(props.theme === 'dark' ? 'light' : 'dark')}
            className="rounded border border-[#303A46] px-3 py-1 text-[#40B6C7]">
            {props.theme === 'dark' ? '深色（当前）' : '浅色（当前）'}
          </button>
        </div>
      </div>
      <div className={`${SURFACE} mt-4 rounded-lg p-5`}>
        <h2 className="text-sm font-semibold">高级与专业视图</h2>
        <p className="mt-1 text-xs text-[#A6B0BE]">专业接口、标准接口与诊断投影；从这里进入完整观察者界面。</p>
        <ul className="mt-3 flex flex-wrap gap-2">
          {advanced.map((a) => (
            <li key={a.id}>
              <a href={`/index.html?view=${a.id}`} className="rounded border border-[#303A46] px-3 py-1 text-xs text-[#40B6C7] hover:underline">
                {a.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
      <div className={`${SURFACE} mt-4 rounded-lg p-5 text-xs text-[#A6B0BE]`}>
        <h2 className="text-sm font-semibold text-[#E8EDF3]">数据与隐私</h2>
        <p className="mt-2">观察者严格只读：本应用不执行、不批准、不重试、不回滚，不写遥测账本。</p>
        <p className="mt-1">快照修订：{props.snap ? props.snap.revision : 'UNKNOWN'}；无快照时所有数值保持 UNKNOWN，不补 0。</p>
      </div>
    </section>
  )
}

function MethodDrawer(props: {
  method: SolutionItem | null
  solutionsState: 'LOADING' | 'OK' | 'UNREACHABLE' | 'BAD'
  solutionsWhy: string | null
  projectName: string | null
  issues: DailyIssueRow[]
  packs: ManualRepairPack[]
  tools: DailyToolRow[]
  onClose: () => void
}) {
  const [target, setTarget] = useState('')
  const [stepsOpen, setStepsOpen] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(true)
  const [copyResult, setCopyResult] = useState<{ ok: boolean; why?: string } | null>(null)
  // 修复包接缝：方法经 issueRefs 指纹对上修复包时，材料用后端渲染的 handoffText；
  // 没对上才回退到方案库方法材料。两种来源都明确标注，不混用。
  const linkedIssue = props.method
    ? props.issues.find((i) => props.method!.issueRefs.includes(i.fingerprint)) ?? null
    : null
  const linkedPack = props.method
    ? props.packs.find((p) => props.method!.issueRefs.some((fp) => p.binds.issueFingerprints.includes(fp))) ?? null
    : null
  const material = useMemo(() => buildHandoverMaterial({
    projectName: props.projectName,
    issueTitle: linkedIssue?.title ?? null,
    method: props.method,
    pack: linkedPack,
    targetTool: target,
  }), [props.projectName, props.method, linkedIssue, linkedPack, target])

  const doCopy = async () => {
    const outcome = await writeClipboardText(material.text)
    setCopyResult(outcome.ok ? { ok: true } : { ok: false, why: outcome.why })
  }
  const doExport = () => {
    const blob = new Blob([material.text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = material.fileName
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40" role="dialog" aria-modal="true" aria-label="方法详情与交接">
      <div className="flex h-full w-[440px] flex-col border-l border-[#303A46] bg-[#171D25]">
        <div className="flex items-start justify-between border-b border-[#303A46] px-5 py-4">
          <div className="min-w-0">
            <p className="text-xs text-[#A6B0BE]">方法详情</p>
            <h2 className="truncate text-base font-semibold">
              {props.method ? (props.method.title ?? props.method.solutionId) : '未找到该方法'}
            </h2>
          </div>
          <button type="button" onClick={props.onClose} aria-label="关闭抽屉" className="text-[#A6B0BE] hover:text-[#E8EDF3]">✕</button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4 text-sm">
          {!props.method ? (
            props.solutionsState === 'OK'
              ? <p className="text-[#A6B0BE]">链接指向的方法在方案库中不存在（不猜测最近的方法）。</p>
              : <p className="text-[#A6B0BE]">方案库{props.solutionsState === 'LOADING' ? '读取中' : '暂无法获取'}：{props.solutionsWhy ?? '等待读取'}。</p>
          ) : (
            <>
              <p className="text-xs text-[#A6B0BE]">
                来源软件：{String(props.method.software.softwareId ?? '未记录')} · 修订 r{props.method.revision ?? '?'} · 状态 {props.method.status ?? 'UNKNOWN'}
                {props.method.recommended ? ' · 已收录推荐' : ' · 候选方法（未验证）'}
              </p>
              <div className="mt-3 rounded border border-[#303A46] bg-[#10141A] p-3">
                <h3 className="text-xs font-semibold text-[#40B6C7]">当前适用性</h3>
                <p className="mt-1 text-xs">{props.method.versionHint?.message ?? '待确认'}</p>
                {props.method.limits.length > 0 && (
                  <ul className="mt-2 list-disc pl-4 text-xs text-[#A6B0BE]">
                    {props.method.limits.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                )}
              </div>
              {props.method.preconditions.length > 0 && (
                <div className="mt-3">
                  <h3 className="text-xs font-semibold">用途与前提</h3>
                  <ul className="mt-1 list-disc pl-4 text-xs text-[#A6B0BE]">
                    {props.method.preconditions.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </div>
              )}
              <div className="mt-3">
                <button type="button" onClick={() => setStepsOpen((o) => !o)} aria-expanded={stepsOpen}
                  className="flex w-full items-center justify-between rounded border border-[#303A46] px-3 py-2 text-left text-xs">
                  给外部工具参考的处理步骤（默认折叠，{props.method.steps.length} 步）
                  <span aria-hidden="true">{stepsOpen ? '收起' : '展开'}</span>
                </button>
                {stepsOpen && (
                  <ol className="mt-2 list-decimal space-y-1 pl-5 text-xs text-[#A6B0BE]">
                    {props.method.steps.map((s, i) => <li key={i}>{s}</li>)}
                  </ol>
                )}
              </div>
              {props.method.risks.length > 0 && (
                <div className="mt-3">
                  <h3 className="text-xs font-semibold">风险</h3>
                  <ul className="mt-1 list-disc pl-4 text-xs text-[#A6B0BE]">
                    {props.method.risks.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </div>
              )}
              {props.method.invalidWhen.length > 0 && (
                <div className="mt-3 rounded border border-amber-400/40 bg-amber-400/5 p-3">
                  <h3 className="text-xs font-semibold text-amber-300">失效条件</h3>
                  <ul className="mt-1 list-disc pl-4 text-xs text-[#A6B0BE]">
                    {props.method.invalidWhen.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
        <div className="border-t border-[#303A46] px-5 py-4">
          <label className="text-xs text-[#A6B0BE]" htmlFor="daily-target-tool">目标交接工具</label>
          <select id="daily-target-tool" value={target} onChange={(e) => setTarget(e.target.value)}
            className="mt-1 w-full rounded border border-[#303A46] bg-[#10141A] px-2 py-1.5 text-sm">
            <option value="">手动复制（未指定工具）</option>
            {props.tools.map((t) => <option key={t.clientId} value={t.displayName}>{t.displayName}</option>)}
          </select>
          <button type="button" onClick={() => setPreviewOpen((o) => !o)} aria-expanded={previewOpen}
            className="mt-2 flex w-full items-center justify-between text-left text-xs text-[#A6B0BE]">
            交接材料预览（{linkedPack ? `来源：修复包 ${linkedPack.packId} · 后端渲染 · 未发送` : '来源：方案库方法'}）
            <span aria-hidden="true">{previewOpen ? '收起' : '展开'}</span>
          </button>
          {previewOpen && (
            <textarea readOnly value={material.text} aria-label="交接材料预览"
              className="mt-1 h-28 w-full resize-y rounded border border-[#303A46] bg-[#10141A] p-2 font-mono text-xs" />
          )}
          <div className="mt-3 flex items-center gap-2">
            <button type="button" onClick={doExport}
              className="rounded border border-[#303A46] px-3 py-1.5 text-sm text-[#A6B0BE] hover:text-[#E8EDF3]">
              导出为文本
            </button>
            <button type="button" onClick={doCopy}
              className="flex-1 rounded bg-[#40B6C7] px-3 py-1.5 text-sm font-medium text-[#10141A]">
              复制给外部工具
            </button>
          </div>
          {copyResult && (
            copyResult.ok
              ? <p role="status" className="mt-2 text-xs text-emerald-400">已写入剪贴板（与预览一致）。</p>
              : <div role="alert" className="mt-2 text-xs text-amber-300">
                  剪贴板不可用：{copyResult.why}。上方预览文本可手动选择复制。
                </div>
          )}
        </div>
      </div>
    </div>
  )
}

// 日常壳（2026-10-24 TRAE 交接包）：M01 项目首页 / M02 项目概览 / M03 问题与经验 /
// M04 方法交接抽屉 / M05 我的工具，一级导航 项目/问题与经验/我的工具，设置底置。
// 数据只来自真实快照、/api/v1/repair-packs 与 /api/v1/solutions；缺数据如实 UNKNOWN。
// 本壳经 ?shell=daily 进入，不替换专业投影壳；高级入口从这里链接过去。
import { useState, useEffect, useMemo, useCallback } from 'react'
import type { SnapshotV3 } from '@/types'
import { fmtTimestamp, repairPacksEndpoint } from '@/lib/api'
import {
  makeHttpRepairPackReader,
  writeClipboardText, type ManualRepairPack, type RepairPacksView,
} from '@/lib/repairPack'
import {
  fetchSolutions, type SolutionSearchView, type SolutionItem,
} from '@/daily/solutionsClient'
import { Rail, TopBar, SectionTitle, StatusPill, IconTile, Chip, MetaItem, TimeIcon, DisabledAction, Link2 } from '@/daily/DailyChrome'
import { ChevronDown, CheckCircle2, CircleAlert, FileText, Filter, Plug, Plus, Sparkles, TriangleAlert } from 'lucide-react'
import {
  dailyProjectCards, dailyIssueRows, dailyToolRows, buildHandoverMaterial,
  type DailyProjectCard, type DailyIssueRow, type DailyToolRow,
} from '@/daily/dailyData'

export type DailyView = 'home' | 'overview' | 'issues' | 'tools' | 'settings'

const DAILY_PARAMS = ['shell', 'dv', 'dp', 'dq', 'dm', 'dtool', 'di'] as const
export type IssueSegment = 'all' | 'open' | 'methods'

function readParams(): { dv: DailyView; dp: string | null; dq: string; dm: string | null; dtool: string | null; di: IssueSegment } {
  try {
    const s = new URLSearchParams(window.location.search)
    const dvRaw = s.get('dv')
    const dv: DailyView = dvRaw === 'overview' || dvRaw === 'issues' || dvRaw === 'tools' || dvRaw === 'settings'
      ? dvRaw : 'home'
    const raw = s.get('di')
    const di: IssueSegment = raw === 'open' || raw === 'methods' ? raw : 'all'
    return { dv, dp: s.get('dp'), dq: s.get('dq') ?? '', dm: s.get('dm'), dtool: s.get('dtool'), di }
  } catch {
    return { dv: 'home', dp: null, dq: '', dm: null, dtool: null, di: 'all' }
  }
}

function writeParams(state: { dv: DailyView; dp: string | null; dq: string; dm: string | null; dtool: string | null; di: IssueSegment }) {
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
  setOrDrop('di', state.di === 'all' ? null : state.di)
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

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        const box = document.getElementById('daily-global-search') as HTMLInputElement | null
        box?.focus()
        box?.select()
      }
      if (e.key === 'Escape') closeMethod()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const transport = error && !snap
    ? { label: '数据源不可用', tone: 'offline' as const }
    : live
      ? { label: '数据源就绪', tone: 'live' as const }
      : snap
        ? { label: '快照未验证', tone: 'unknown' as const }
        : { label: '等待快照', tone: 'unknown' as const }
  const shell = (
    <div className="flex h-screen flex-col bg-[#10141A] text-[#E8EDF3]" data-shell="daily">
      <TopBar query={state.dq} onQuery={(v) => navigate({ dq: v })} hudHint={null} />
      <div className="flex min-h-0 flex-1">
        <Rail
          view={state.dv === 'overview' ? 'home' : state.dv}
          onNavigate={(v) => navigate({ dv: v, dp: v === 'home' ? null : state.dp })}
          transportLabel={transport.label} transportTone={transport.tone}
        />

        <div className="flex min-h-0 flex-1 flex-col">
          {searchDisabledNote && (
            <div role="alert" className="border-b border-[#303A46] bg-[#171D25] px-5 py-2 text-xs text-amber-300">
              {searchDisabledNote}
            </div>
          )}
          <main className="min-h-0 flex-1 overflow-y-auto px-6 py-5" id="daily-content">
            {state.dv === 'home' && (
              <HomeView cards={filteredProjects} totalCount={cards.length} onOpen={openProject}
                query={state.dq} onQuery={(v) => navigate({ dq: v })} />
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
                solutions={solutions}
                segment={state.di}
                query={state.dq}
                onQuery={(dq) => navigate({ dq })}
                onSegment={(di) => navigate({ di })}
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
  // The caption cluster and the drag surface live in TopBar (DailyChrome), because the
  // desktop main window is borderless (decorations:false) and the default entry is this shell.
  return shell
}

function HomeView(props: {
  cards: DailyProjectCard[]; totalCount: number; onOpen: (id: string) => void
  query: string; onQuery: (v: string) => void
}) {
  return (
    <section aria-label="项目首页" data-view="m01">
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">项目</h1>
        <Chip>{props.totalCount} 个已注册项目</Chip>
        <div className="ml-auto flex items-center gap-2">
          <span className="relative inline-flex items-center">
            <Filter size={13} aria-hidden="true" className="pointer-events-none absolute left-2.5 text-[#A6B0BE]" />
            <input
              type="search" value={props.query} onChange={(e) => props.onQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Escape') { e.preventDefault(); props.onQuery('') } }}
              aria-label="按名称过滤项目" placeholder="按名称过滤…"
              className="h-8 w-[212px] rounded-md border pl-8 pr-12 text-sm outline-none"
              style={{ borderColor: '#303A46', background: '#10141A', color: '#E8EDF3' }}
            />
            <kbd className="pointer-events-none absolute right-2 rounded border px-1 text-xs"
              style={{ borderColor: '#303A46', color: '#A6B0BE' }}>ESC</kbd>
          </span>
          <DisabledAction label="添加项目" reason="观察者只读：登记项目由项目侧完成"
            icon={<Plus size={13} aria-hidden="true" />} />
        </div>
      </div>
      {props.cards.length === 0 ? (
        <div className={`${SURFACE} rounded-lg p-6 text-sm text-[#A6B0BE]`}>
          {props.totalCount === 0
            ? '快照中没有已注册项目（实测为 0，不是缺字段）。'
            : '没有匹配当前搜索的项目。清除搜索词可恢复完整列表。'}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
          {props.cards.map((card) => (
            <article key={card.projectId} data-landmark="project-card"
              className="flex flex-col rounded-xl border bg-[#171D25] p-5"
              style={{ borderColor: '#303A46' }}>
              <div className="flex items-start gap-3">
                <IconTile label={card.displayName} />
                <div className="min-w-0 flex-1">
                  <h2 className="truncate text-[15px] font-semibold">{card.displayName}</h2>
                  <p className="mt-0.5 truncate font-mono text-xs text-[#A6B0BE]">{card.projectId}</p>
                </div>
                <StatusPill status={card.status} />
              </div>
              <div className="mt-4 rounded-lg bg-[#1C2430] p-3">
                <div className="text-xs text-[#A6B0BE]">最近变化</div>
                <p className="mt-1 text-sm">
                  {card.latestChange ? fmtTimestamp(card.latestChange) : '待确认'}
                </p>
                {card.attentionNote && (
                  <p className="mt-2 text-xs text-amber-300">{card.attentionNote}</p>
                )}
              </div>
              <p className="mt-3 flex flex-wrap items-center gap-1.5 text-xs text-[#A6B0BE]">
                <Link2 size={13} aria-hidden="true" />关联工具：
                {card.relatedTools.length
                  ? card.relatedTools.map((t) => <Chip key={t}>{t}</Chip>)
                  : <span>未记录</span>}
                {card.openIssueCount !== null && card.openIssueCount > 0 && (
                  <Chip tone="warn">{card.openIssueCount} 个当前问题</Chip>
                )}
              </p>
              <div className="mt-4 flex items-center justify-between border-t border-[#303A46] pt-3">
                <MetaItem icon={<TimeIcon />}>
                  更新：{card.updatedAt ? fmtTimestamp(card.updatedAt) : 'UNKNOWN'}
                </MetaItem>
                <button type="button" onClick={() => props.onOpen(card.projectId)}
                  className="text-sm text-[#40B6C7] hover:underline">
                  进入项目概览 →
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
      <p className="mt-5 text-xs text-[#A6B0BE]">
        本页只投影真实快照；缺的字段保持 UNKNOWN，不用演示数据填满。
      </p>
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
      <section aria-label="项目概览" data-view="m02">
        <button type="button" onClick={props.onBack}
          className="rounded border border-[#303A46] bg-[#1C2430] px-3 py-1.5 text-sm text-[#40B6C7]">
          ← 所有项目
        </button>
        <div className={`${SURFACE} mt-4 rounded-lg p-6 text-sm text-[#A6B0BE]`}>
          链接指向的项目在本机投影中不存在（不猜测最近的项目）。
        </div>
      </section>
    )
  }
  return (
    <section aria-label="项目概览" data-view="m02">
      <button type="button" onClick={props.onBack}
        className="rounded border border-[#303A46] bg-[#1C2430] px-3 py-1.5 text-sm text-[#40B6C7]">
        ← 所有项目
      </button>
      <header className="mt-3 rounded-xl border border-[#303A46] bg-[#171D25] p-5">
        <div className="flex flex-wrap items-start gap-3">
          <IconTile label={props.card.displayName} size={40} />
          <div className="min-w-0 flex-1">
            <h1 className="flex flex-wrap items-center gap-2 text-xl font-semibold">
              {props.card.displayName}
              <Chip>版本 UNKNOWN</Chip>
              <StatusPill status={props.card.status} />
            </h1>
            <p className="mt-2 text-sm text-[#A6B0BE]">
              {props.card.attentionNote
                ?? `本轮状态由真实快照投影；关联工具：${props.card.relatedTools.length ? props.card.relatedTools.join('、') : '未记录'}。`}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-4">
              <MetaItem icon={<TimeIcon />}>
                确认时间：{props.card.updatedAt ? fmtTimestamp(props.card.updatedAt) : 'UNKNOWN'}
              </MetaItem>
              <MetaItem icon={<Link2 size={13} aria-hidden="true" />}>
                关联工具：{props.card.relatedTools.length ? props.card.relatedTools.join('、') : '未记录'}
              </MetaItem>
            </div>
          </div>
          <DisabledAction label="打开对应工具" reason="观察者只读：不启动外部软件" primary />
        </div>
      </header>
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className={`${SURFACE} rounded-lg p-5 ${props.issues.length ? 'border-t-2 border-t-amber-400' : ''}`}>
          <h2 className="flex items-center gap-2 text-sm font-semibold">
            <TriangleAlert size={15} aria-hidden="true" className={props.issues.length ? 'text-amber-300' : 'text-[#A6B0BE]'} />
            需要关注的事项
          </h2>
          {props.issues.length === 0 ? (
            <p className="mt-2 text-xs text-[#A6B0BE]">本项目当前没有打开的问题（实测，非推断）。</p>
          ) : (
            <ul className="mt-3 space-y-3">
              {props.issues.map((issue) => (
                <li key={issue.fingerprint} className="rounded border border-[#303A46] bg-[#10141A] p-3">
                  <div className="text-sm font-medium">《{issue.title}》</div>
                  <p className="mt-1 text-xs text-[#A6B0BE]">{issue.classLabel} · {issue.priority} · 最近 {fmtTimestamp(issue.lastSeenAt)}</p>
                  <div className="mt-2 flex items-start justify-between gap-2 rounded bg-[#1C2430] p-2">
                    <span className="flex items-start gap-2 text-xs">
                      <Plug size={13} aria-hidden="true" className="mt-0.5 text-[#40B6C7]" />
                      <span>
                        <span className="text-[#40B6C7]">外部工具反馈</span>
                        <span className="block text-[#A6B0BE]">
                          {issue.hasPack ? '已有修复包草稿（未发送），可在问题与经验页交接。' : '尚无修复包；可在问题与经验页查看可参考方法。'}
                        </span>
                      </span>
                    </span>
                    <Chip tone="warn">未核验</Chip>
                  </div>
                  <button type="button" onClick={() => issue.hasPack && props.onOpenMethod(issue.packId ?? '')}
                    className="mt-2 rounded bg-[#40B6C7] px-3 py-1.5 text-xs font-medium text-[#10141A] disabled:cursor-not-allowed disabled:bg-[#1C2430] disabled:text-[#A6B0BE]"
                    disabled={!issue.hasPack}
                    title={issue.hasPack ? '打开该问题的交接材料' : '本问题还没有修复包草稿'}>
                    查看参考方法 →
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className={`${SURFACE} rounded-lg p-5`}>
          <h2 className="flex items-center gap-2 text-sm font-semibold">
            <Sparkles size={15} aria-hidden="true" className="text-[#40B6C7]" />可参考的历史经验
          </h2>
          {!props.solutions ? (
            <p className="mt-2 text-xs text-[#A6B0BE]">方案库状态：读取中（不预填结果）。</p>
          ) : props.solutions.status === 'SOURCE_ABSENT' ? (
            <p className="mt-2 text-xs text-[#A6B0BE]">方案库暂无法获取：{props.solutions.reason}</p>
          ) : props.solutions.results.length === 0 ? (
            <p className="mt-2 text-xs text-[#A6B0BE]">{props.solutions.reason}</p>
          ) : (
            <>
              <p className="mt-1 text-xs text-[#A6B0BE]">发现 {props.solutions.results.length} 条相似经验可供参考</p>
              <ul className="mt-3 space-y-3">
                {props.solutions.results.slice(0, 3).map((m) => (
                  <li key={m.solutionId} className="rounded border border-[#303A46] bg-[#10141A] p-3">
                    <div className="text-sm font-medium">《{m.title ?? m.solutionId}》</div>
                    <p className="mt-1 text-xs text-[#A6B0BE]">
                      项目 {String(m.software.softwareId ?? '未记录')} · {m.versionHint?.message ?? '适用性待确认'}
                    </p>
                    <button type="button" onClick={() => props.onOpenMethod(m.solutionId)}
                      className="mt-2 w-full rounded border border-[#303A46] bg-[#1C2430] px-3 py-1.5 text-left text-xs text-[#40B6C7]">
                      查看该方法详情 →
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
      <div className={`${SURFACE} mt-4 rounded-lg`}>
        <button type="button" onClick={() => setTechOpen((o) => !o)} aria-expanded={techOpen}
          className="flex w-full items-center justify-between px-5 py-3 text-left text-sm">
          <span className="flex items-center gap-2">
            <FileText size={15} aria-hidden="true" className="text-[#A6B0BE]" />
            查看详细依据与诊断记录
            <span className="text-xs text-[#A6B0BE]">（{techOpen ? '已展开' : '已收起'}，点击{techOpen ? '收起' : '展开'}）</span>
          </span>
          <ChevronDown size={15} aria-hidden="true"
            className={techOpen ? 'rotate-180 transition-transform' : 'transition-transform'} />
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
  solutions: SolutionSearchView | null
  segment: IssueSegment
  query: string
  onQuery: (q: string) => void
  onSegment: (s: IssueSegment) => void
  onOpenMethod: (id: string) => void
  onOpenProject: (id: string) => void
  feedback: Record<string, { verdict: string; note: string }>
  onFeedback: (fingerprint: string, verdict: string) => void
  onFeedbackNote: (fingerprint: string, note: string) => void
}) {
  const [expanded, setExpanded] = useState<string | null>(null)
  const summary = props.issuesSummary
  const visible = props.segment === 'methods' ? [] : props.rows
  const methods = props.segment === 'open' ? [] : (props.solutions?.results ?? [])
  const matchedMethod = (issue: DailyIssueRow) =>
    (props.solutions?.results ?? []).find((m) => m.issueRefs.includes(issue.fingerprint)) ?? null

  return (
    <section aria-label="问题与经验" data-view="m03">
      <p className="flex items-center gap-1.5 text-xs uppercase tracking-wider text-[#40B6C7]">
        <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-[#40B6C7]" />
        Diagnostics &amp; Knowledge Hub
      </p>
      <h1 className="mt-1 text-xl font-semibold">问题与经验</h1>
      <p className="mt-1 text-xs text-[#A6B0BE]">
        查看正在影响软件项目的问题，以及可供参考的过往解法。相似表现不等于相同根因。
      </p>
      {summary && (
        <p className="mt-2 text-xs text-[#A6B0BE]">
          来源 {summary.sourcesRead} 个 · 扫描 {summary.rowsScanned} 行 · 产出 {summary.emittedCount} 条
          {summary.truncated ? ' · 已截断' : summary.complete === false ? ' · 覆盖不完整' : ''}
        </p>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2 rounded-lg border border-[#303A46] bg-[#171D25] p-2">
        <div role="group" aria-label="问题筛选分段" className="flex items-center gap-1">
          {([['all', '全部'], ['open', '需要处理'], ['methods', '方法与经验']] as [IssueSegment, string][]).map(([id, label]) => (
            <button key={id} type="button" onClick={() => props.onSegment(id)} aria-pressed={props.segment === id}
              className={`rounded px-3 py-1 text-xs ${props.segment === id
                ? 'bg-[#40B6C7] font-medium text-[#10141A]' : 'text-[#A6B0BE] hover:text-[#E8EDF3]'}`}>
              {label}
            </button>
          ))}
        </div>
        <span className="relative ml-auto inline-flex items-center">
          <Filter size={13} aria-hidden="true" className="pointer-events-none absolute left-2.5 text-[#A6B0BE]" />
          <input type="search" value={props.query} onChange={(e) => props.onQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Escape') { e.preventDefault(); props.onQuery('') } }}
            aria-label="检索标题、错误或经验" placeholder="检索标题、错误或经验…"
            className="h-7 w-[212px] rounded border pl-8 pr-3 text-xs outline-none"
            style={{ borderColor: '#303A46', background: '#10141A', color: '#E8EDF3' }} />
        </span>
        <span className="text-xs text-[#A6B0BE]">
          共 {props.segment === 'methods' ? methods.length : visible.length} 条
          {props.totalCount !== null ? ` · 快照产出 ${props.totalCount} 条问题` : ''}
        </span>
      </div>

      <ul className="mt-4 space-y-3">
        {visible.length === 0 && props.segment !== 'methods' && (
          <li className={`${SURFACE} rounded-lg p-6 text-sm text-[#A6B0BE]`}>
            {props.totalCount === 0
              ? '当前没有打开的问题（实测，非推断）。'
              : '没有匹配当前搜索的问题。'}
          </li>
        )}
        {visible.map((issue) => {
          const open = expanded === issue.fingerprint
          const method = matchedMethod(issue)
          return (
            <li key={issue.fingerprint} data-landmark="issue-row"
              className={`${SURFACE} rounded-lg border-l-4 ${issue.priority === 'P1' ? 'border-l-amber-400' : 'border-l-[#303A46]'} p-4`}>
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <Chip tone="warn">当前需要处理</Chip>
                {issue.projectId && (
                  <button type="button" onClick={() => props.onOpenProject(issue.projectId as string)}
                    className="rounded border border-[#303A46] bg-[#10141A] px-1.5 py-0.5 text-xs text-[#40B6C7] hover:underline">
                    {issue.projectId}
                  </button>
                )}
                <MetaItem icon={<TimeIcon />}>{issue.lastSeenAt ? fmtTimestamp(issue.lastSeenAt) : 'UNKNOWN'}</MetaItem>
                <button type="button" onClick={() => setExpanded(open ? null : issue.fingerprint)}
                  aria-expanded={open} className="ml-auto text-xs text-[#40B6C7]">
                  {open ? '收起' : '展开'}
                </button>
              </div>
              <button type="button" onClick={() => setExpanded(open ? null : issue.fingerprint)}
                aria-expanded={open} className="mt-2 block w-full text-left text-sm font-medium">
                《{issue.title}》
              </button>
              {issue.detail && <p className="mt-1 text-xs text-[#A6B0BE]">{issue.detail}</p>}
              <p className="mt-1 text-xs text-[#A6B0BE]">{issue.classLabel} · {issue.priority}</p>

              {open && (
                <div className="mt-3 border-t border-[#303A46] pt-3">
                  <div className="text-xs text-[#A6B0BE]">
                    证据位置：{issue.fingerprint.slice(0, 24)}…（同类表现未必同因）
                  </div>
                  <div className="mt-3 rounded-lg border border-[#303A46] bg-[#10141A] p-3">
                    <SectionTitle right={method ? '命中已收录方案' : '未命中已验证方案'}>
                      智能经验推断 · 类似场景推荐方案
                    </SectionTitle>
                    <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-3">
                      <div className="rounded border border-[#303A46] bg-[#1C2430] p-2">
                        <div className="text-xs text-[#A6B0BE]">1 当时的情况</div>
                        <p className="mt-1 text-xs">
                          “{method?.preconditions[0] ?? issue.detail ?? '未记录'}”
                        </p>
                      </div>
                      <div className="rounded border border-[#303A46] bg-[#1C2430] p-2">
                        <div className="text-xs text-[#A6B0BE]">2 采用的方法</div>
                        <p className="mt-1 text-xs">“{method?.steps[0] ?? '待确认'}”</p>
                      </div>
                      <div className="rounded border border-[#303A46] bg-[#1C2430] p-2">
                        <div className="text-xs text-[#A6B0BE]">3 实际结果</div>
                        <p className="mt-1 text-xs">
                          “{method ? '已核验关闭（来源记录未提供结果原文）' : '待确认'}”
                        </p>
                      </div>
                    </div>
                    {method && (
                      <button type="button" onClick={() => props.onOpenMethod(method.solutionId)}
                        className="mt-3 rounded bg-[#40B6C7] px-3 py-1.5 text-xs font-medium text-[#10141A]">
                        查看方法 →
                      </button>
                    )}
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

        {methods.map((m) => (
          <li key={m.solutionId} data-landmark="method-row"
            className={`${SURFACE} flex flex-wrap items-center gap-3 rounded-lg p-4`}>
            <IconTile label={String(m.software.softwareId ?? '方法')} size={32} />
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-medium">《{m.title ?? m.solutionId}》</span>
                <Chip tone={m.recommended ? 'accent' : 'neutral'}>
                  {m.recommended ? '已收录推荐' : '候选方法'}
                </Chip>
                <span className="text-xs text-[#A6B0BE]">{String(m.software.softwareId ?? '未记录')}</span>
              </div>
              <p className="mt-1 text-xs text-[#A6B0BE]">{m.versionHint?.message ?? '适用性待确认'}</p>
            </div>
            <button type="button" onClick={() => props.onOpenMethod(m.solutionId)}
              className="text-xs text-[#40B6C7] hover:underline">查看方法 &gt;</button>
          </li>
        ))}
        {props.segment === 'methods' && methods.length === 0 && (
          <li className={`${SURFACE} rounded-lg p-6 text-sm text-[#A6B0BE]`}>
            {props.solutions === null ? '方案库读取中（不预填结果）。' : `方案库：${props.solutions.reason}`}
          </li>
        )}
      </ul>
    </section>
  )
}

function ToolsView(props: { tools: DailyToolRow[]; selected: DailyToolRow | null; onSelect: (id: string) => void }) {
  const quickAccess = [
    { id: 'usage', title: '使用方法', desc: '查看向该工具提供受控上下文与排查指引的建议做法' },
    { id: 'rules', title: '提示词与规则', desc: '查看推荐的交付格式模板与目录约束规则' },
    { id: 'faq', title: '常见问题', desc: '查看连接中断或排查超时时的常见处理问答' },
  ]
  return (
    <section aria-label="我的工具" data-view="m05">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-semibold">我的工具</h1>
          <p className="mt-1 text-xs text-[#A6B0BE]">管理外部 AI 与本地开发工具的连接身份与使用辅助。</p>
        </div>
        <DisabledAction label="检测环境工具" reason="观察者只读：不发起探测运行" />
        <DisabledAction label="登记新工具" reason="观察者只读：登记由项目侧完成" />
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        <div className={`${SURFACE} rounded-lg p-3`}>
          <div className="mb-2 flex items-center justify-between px-1 text-xs uppercase tracking-wider text-[#A6B0BE]">
            <span>已登记工具</span><span>FILTER: ALL</span>
          </div>
          <ul className="space-y-2" aria-label="工具列表">
            {props.tools.length === 0 && (
              <li className="p-4 text-xs text-[#A6B0BE]">
                快照未携带适配器能力卡（来源缺失，不是 0 个工具）。
              </li>
            )}
            {props.tools.map((tool) => {
              const active = props.selected?.clientId === tool.clientId
              return (
                <li key={tool.clientId}>
                  <button type="button" onClick={() => props.onSelect(tool.clientId)}
                    aria-current={active ? 'true' : undefined}
                    className={`relative w-full rounded-lg border p-3 text-left ${active
                      ? 'border-[#40B6C7] bg-[#1C2430]' : 'border-[#303A46] bg-[#171D25]'}`}>
                    {active && (
                      <span aria-hidden="true" className="absolute left-0 top-3 bottom-3 w-[2px] rounded-full bg-[#40B6C7]" />
                    )}
                    <div className="flex items-start gap-2">
                      <IconTile label={tool.displayName} size={28} tone="surface" />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="truncate text-sm font-medium">{tool.displayName}</span>
                          <Chip tone={tool.connection.includes('失败') || tool.connection.includes('未连接') ? 'warn' : 'accent'}>
                            {tool.connection.includes('失败') || tool.connection.includes('未连接') ? '未连接' : '已连接'}
                          </Chip>
                        </div>
                        <p className="mt-0.5 truncate text-xs text-[#A6B0BE]">{tool.version ?? '版本 UNKNOWN'}</p>
                      </div>
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <MetaItem icon={<TimeIcon />}>
                        {tool.observedAt ? fmtTimestamp(tool.observedAt) : 'UNKNOWN'}
                      </MetaItem>
                      <span className="text-xs uppercase tracking-wide"
                        style={{ color: active ? '#40B6C7' : '#A6B0BE' }}>
                        {active ? 'SELECTED' : 'IDLE'}
                      </span>
                    </div>
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
        <div className="space-y-4">
          <div className={`${SURFACE} rounded-lg p-5`}>
            {!props.selected ? (
              <p className="text-sm text-[#A6B0BE]">左侧选择一个工具查看详情。</p>
            ) : (
              <div className="flex flex-wrap items-start gap-3">
                <IconTile label={props.selected.displayName} size={40} />
                <div className="min-w-0 flex-1">
                  <h2 className="flex flex-wrap items-center gap-2 text-lg font-semibold">
                    {props.selected.displayName}
                    <Chip tone="accent">{props.selected.connection}</Chip>
                  </h2>
                  <p className="mt-1 text-xs text-[#A6B0BE]">
                    声明版本：{props.selected.version ?? 'UNKNOWN'} · 写入策略：{props.selected.writePolicy || 'UNKNOWN'}
                  </p>
                </div>
                <DisabledAction label={`打开 ${props.selected.displayName} 外部客户端`}
                  reason="观察者只读：不启动外部软件" primary />
                <div className="mt-4 grid w-full grid-cols-1 gap-3 md:grid-cols-3">
                  <div className="rounded border border-[#303A46] bg-[#10141A] p-3">
                    <dt className="text-xs text-[#A6B0BE]">当前可用能力</dt>
                    <dd className="mt-1 text-sm">{props.selected.capabilitySentence}</dd>
                  </div>
                  <div className="rounded border border-[#303A46] bg-[#10141A] p-3">
                    <dt className="text-xs text-[#A6B0BE]">关联项目</dt>
                    <dd className="mt-1 text-sm">
                      {props.selected.relatedProjects.length ? props.selected.relatedProjects.join('、') : '未记录'}
                    </dd>
                  </div>
                  <div className="rounded border border-[#303A46] bg-[#10141A] p-3">
                    <dt className="text-xs text-[#A6B0BE]">最近更新</dt>
                    <dd className="mt-1 text-sm">
                      {props.selected.observedAt ? fmtTimestamp(props.selected.observedAt) : 'UNKNOWN'}
                    </dd>
                  </div>
                </div>
              </div>
            )}
          </div>
          <div className={`${SURFACE} rounded-lg p-5`}>
            <SectionTitle right="QUICK ACCESS">使用辅助</SectionTitle>
            <ul className="mt-3 divide-y divide-[#303A46]">
              {quickAccess.map((row) => (
                <li key={row.id}>
                  <div className="flex items-center gap-3 py-3">
                    <FileText size={15} aria-hidden="true" className="shrink-0 text-[#40B6C7]" />
                    <div className="min-w-0 flex-1">
                      <div className="text-sm">{row.title}</div>
                      <p className="text-xs text-[#A6B0BE]">{row.desc}</p>
                    </div>
                    <ChevronDown size={15} aria-hidden="true" className="-rotate-90 text-[#A6B0BE]" />
                  </div>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-[#A6B0BE]">
              本页不修改对方全局配置；三条辅助内容是只读指引，不代为执行。
            </p>
          </div>
          <div className={`${SURFACE} rounded-lg p-5`}>
            <div className="flex flex-wrap items-center gap-3">
              <div className="min-w-0 flex-1">
                <h3 className="flex items-center gap-2 text-sm font-semibold">
                  连接配置与设置 <Chip>高级入口</Chip>
                </h3>
                <p className="mt-1 text-xs text-[#A6B0BE]">
                  如需查看本地通信端口、工作区路径映射与授权状态，请进入专业投影的设置面板；本页不代为修改。
                </p>
              </div>
              <a href="/index.html?view=settings"
                className="inline-flex items-center gap-1.5 rounded-lg border border-[#303A46] bg-[#10141A] px-3 py-1.5 text-sm text-[#40B6C7]">
                进入工具设置面板 →
              </a>
            </div>
          </div>
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

function StepRow(props: { index: number; step: string; detail: string | null; open: boolean; onToggle: () => void }) {
  const num = String(props.index + 1).padStart(2, '0')
  const number = (
    <span className="shrink-0 rounded bg-[#171D25] px-1.5 py-0.5 text-xs font-semibold text-[#40B6C7]">
      {num}
    </span>
  )
  const title = <span className="min-w-0 flex-1 text-xs">{props.step}</span>
  if (!props.detail) {
    return (
      <li className="rounded-lg border border-[#303A46] bg-[#10141A]">
        <div className="flex items-center gap-3 px-3 py-2">{number}{title}</div>
      </li>
    )
  }
  return (
    <li className="rounded-lg border border-[#303A46] bg-[#10141A]">
      <button type="button" onClick={props.onToggle} aria-expanded={props.open}
        className="flex w-full items-center gap-3 px-3 py-2 text-left">
        {number}{title}
        <Chip tone="warn">含风险提示</Chip>
        <ChevronDown size={14} aria-hidden="true"
          className={`shrink-0 text-[#A6B0BE] transition-transform ${props.open ? 'rotate-180' : ''}`} />
      </button>
      {props.open && (
        <p className="border-t border-[#303A46] px-3 py-2 text-xs text-[#A6B0BE]">
          风险：{props.detail}
        </p>
      )}
    </li>
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
  // The reference opens the first step that carries detail; a step with nothing to expand
  // renders no toggle at all, so the row never promises an interaction it cannot deliver.
  // The default is derived on every render, not captured once in useState: on a cold open the
  // method arrives after the first render, and a captured default would leave risk text hidden.
  const [chosenStep, setChosenStep] = useState<number | undefined>(undefined)
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

  const risks = props.method?.risks ?? []
  const firstDetailed = risks.findIndex((r) => !!r)
  const stepIsOpen = (i: number) => (chosenStep === undefined
    ? i === firstDetailed : chosenStep === i)
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
        <div className="flex items-start justify-between gap-3 border-b border-[#303A46] px-5 py-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <Chip tone="accent">经验详情</Chip>
              <Chip>来自 {props.method ? String(props.method.software.softwareId ?? '未记录') : '方案库'}</Chip>
            </div>
            <h2 className="mt-2 truncate text-base font-semibold">
              {props.method ? `《${props.method.title ?? props.method.solutionId}》` : '未找到该方法'}
            </h2>
            <p className="mt-1 text-xs text-[#A6B0BE]">
              {props.method
                ? `${props.method.recommended ? '已收录推荐' : '候选方法（未验证）'} · 修订 r${props.method.revision ?? '?'} · 状态 ${props.method.status ?? 'UNKNOWN'}`
                : '链接可能指向未收录的方法'}
            </p>
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
              <SectionTitle>方法背景与历史成效</SectionTitle>
              <div className="mt-2 space-y-2">
                <div className="rounded-lg border border-[#303A46] bg-[#10141A] p-3">
                  <div className="flex items-center gap-1.5 text-xs text-[#A6B0BE]">
                    <CircleAlert size={13} aria-hidden="true" className="shrink-0 text-amber-300" />背景什么问题
                  </div>
                  <p className="mt-1 text-xs">
                    {props.method.preconditions.length
                      ? props.method.preconditions.join('；')
                      : '来源记录未提供前提条件'}
                  </p>
                </div>
                <div className="rounded-lg border border-[#303A46] bg-[#10141A] p-3">
                  <div className="flex items-center gap-1.5 text-xs text-[#A6B0BE]">
                    <CheckCircle2 size={13} aria-hidden="true" className="shrink-0 text-emerald-400" />过去取得了什么结果
                  </div>
                  <p className="mt-1 text-xs">
                    {props.method.recommended
                      ? '该方案已被收录为推荐修订（结果原文未在来源记录中提供，不代写）'
                      : '未核验：候选方法，结果待确认'}
                  </p>
                </div>
              </div>

              <div className="mt-4">
                <SectionTitle right={props.method.versionHint?.message ?? '适用性待确认'} rightTone="chip">
                  {props.projectName ? `对当前 ${props.projectName} 的适用性` : '对当前项目的适用性'}
                </SectionTitle>
                <p className="mt-2 text-xs text-[#A6B0BE]">{props.method.limits.join('；') || '来源未记录限制条件'}</p>
                {props.method.invalidWhen.length > 0 && (
                  <div className="mt-2 rounded-lg border border-amber-400/40 bg-amber-400/5 p-3">
                    <div className="text-xs font-semibold text-amber-300">失效条件</div>
                    <ul className="mt-1 list-disc pl-4 text-xs text-[#A6B0BE]">
                      {props.method.invalidWhen.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                  </div>
                )}
              </div>

              <div className="mt-4">
                <SectionTitle right={`供工具执行 · 共 ${props.method.steps.length} 步`}>
                  给外部工具参考的处理步骤
                </SectionTitle>
                <p className="mt-1 text-xs text-[#A6B0BE]">
                  以下为准备交由外部工具（如 {target || '手动复制'}）执行的专业排查指令；
                  带风险提示的步骤可展开查看该提示原文。
                </p>
                <ol className="mt-2 space-y-2">
                  {props.method.steps.map((s, i) => (
                    <StepRow key={i} index={i} step={s} detail={risks[i] ?? null}
                      open={stepIsOpen(i)}
                      onToggle={() => setChosenStep(stepIsOpen(i) ? -1 : i)} />
                  ))}
                  {props.method.steps.length === 0 && (
                    <li className="rounded-lg border border-[#303A46] bg-[#10141A] px-3 py-2 text-xs text-[#A6B0BE]">
                      来源记录未提供步骤（不代写步骤）。
                    </li>
                  )}
                </ol>
              </div>

              {linkedPack && (
                <div className="mt-4 rounded-lg border border-[#303A46] bg-[#10141A] p-3">
                  <SectionTitle right="后端渲染 · 未发送">修复包交接文本</SectionTitle>
                  <p className="mt-1 text-xs text-[#A6B0BE]">来源：修复包 {linkedPack.packId}</p>
                </div>
              )}
            </>
          )}
        </div>
        <div className="border-t border-[#303A46] px-5 py-4">
          <label className="text-xs text-[#A6B0BE]" htmlFor="daily-target-tool">
            目标交接工具 <span className="ml-1">复制后在对应工具中粘贴</span>
          </label>
          <select id="daily-target-tool" value={target} onChange={(e) => setTarget(e.target.value)}
            className="mt-1 w-full rounded border border-[#303A46] bg-[#10141A] px-2 py-1.5 text-sm">
            <option value="">手动复制（未指定工具）</option>
            {props.tools.map((t) => <option key={t.clientId} value={t.displayName}>{t.displayName}</option>)}
          </select>
          <button type="button" onClick={() => setPreviewOpen((o) => !o)} aria-expanded={previewOpen}
            className="mt-2 flex w-full items-start justify-between gap-2 text-left text-xs text-[#A6B0BE]">
            <span className="min-w-0">
              交接材料预览（{linkedPack ? `来源：修复包 ${linkedPack.packId} · 后端渲染 · 未发送` : '来源：方案库方法'}）
            </span>
            <span aria-hidden="true" className="shrink-0 whitespace-nowrap">{previewOpen ? '收起' : '展开'}</span>
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

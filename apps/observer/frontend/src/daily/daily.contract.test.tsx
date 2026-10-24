// 2026-10-24 TRAE 交接包 · 日常壳与 HUD 四态的契约测试。
// 钉住提示词 §13 的真实回归问题：四主入口＋设置底置、UNKNOWN 不补 0、
// 不同方法/工具对应各自记录、预览＝复制＝导出同一材料、反馈是内存态并明说刷新丢失。
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, cleanup, act, fireEvent } from '@testing-library/react'

const mockSnap = {
  schemaVersion: 'workflow/snapshot/v3',
  revision: 7,
  generatedAt: '2026-10-24T00:00:00Z',
  sourceWatermark: '2026-10-24T00:00:00Z',
  transport: { transportState: 'LIVE', freshnessState: 'FRESH', connectedSince: null, eventsUrl: null },
  coverage: { numerator: 1, denominator: 1, scope: 'unit' },
  governance: {
    state: 'CLEAN',
    families: {
      rules: { state: 'CLEAN', current: null, drift: 0 },
      skills: { state: 'CLEAN', current: null, drift: 0 },
      memory: { state: 'CLEAN', current: null, drift: 0 },
      adapters: { state: 'CLEAN', current: null, drift: 0 },
    },
  },
  workspace: {},
  projects: [
    {
      projectId: 'proj-a', displayName: '示例项目甲', agentPlatform: 'qoder', identityState: 'MATCHED',
      activityState: 'ACTIVE', attentionState: 'NONE', activeExecutionCount: 1, workingAreas: [],
      visibility: 'private', quality: 'REAL', lastStrongEvidenceAt: '2026-10-24T00:00:00Z',
      repositories: [], git: { localSha: null, remoteSha: null, matchState: 'NO_LOCAL_CLAIM', branch: null, dirtyCount: null, observedAt: null, quality: null, freshness: null, sourceRef: null, sourceProjectId: null },
      token: { inputTokens: null, outputTokens: null, totalTokens: null, costQuality: 'UNKNOWN' },
      ci: [], executionIds: ['e1'], sourceRefs: [],
    },
    {
      projectId: 'proj-b', displayName: '示例项目乙', agentPlatform: 'codex', identityState: 'MATCHED',
      activityState: 'REGISTERED', attentionState: 'NONE', activeExecutionCount: 0, workingAreas: [],
      visibility: 'private', quality: 'REAL', lastStrongEvidenceAt: null,
      repositories: [], git: { localSha: null, remoteSha: null, matchState: 'NO_LOCAL_CLAIM', branch: null, dirtyCount: null, observedAt: null, quality: null, freshness: null, sourceRef: null, sourceProjectId: null },
      token: { inputTokens: null, outputTokens: null, totalTokens: null, costQuality: 'UNKNOWN' },
      ci: [], executionIds: [], sourceRefs: [],
    },
  ],
  executions: [
    { executionId: 'e1', anchorProjectId: 'proj-a', workingArea: null, state: 'WAITING_USER', stateQuality: 'REAL', agent: 'qoder', sessionId: null, sourceRef: null },
  ],
  tasks: {},
  tokenSummary: { inputTokens: null, outputTokens: null, totalTokens: null, costQuality: 'UNKNOWN' },
  git: { localSha: null, remoteSha: null, ciSha: null, matchState: 'NO_LOCAL_CLAIM' },
  ci: [],
  sourceRefs: [],
  issues: [
    {
      schemaVersion: 'workflow/issue/v1', fingerprint: 'fp-aaa', class: 'SOURCE_FAILURE', projectId: 'proj-a',
      subject: '示例问题：采集器连续失败', origin: 'collector', evidenceRef: 'telemetry_events', priority: 'P1',
      priorityRule: 'P1: source failure', firstSeenAt: '2026-10-23T00:00:00Z', lastSeenAt: '2026-10-24T00:00:00Z',
      occurrences: 3, status: 'OPEN', softwareId: null, softwareVersion: null, softwareVersionSource: 'source-names-no-software',
    },
  ],
  issuesSummary: {
    schemaVersion: 'worklab/issues-summary/v1', sourcesRead: 2, sourcesAbsent: 0, rowsScanned: 10,
    distinctIssueCount: 1, emittedCount: 1, omittedCount: 0, foldedOccurrences: 3, cap: 200, truncated: false,
    complete: true, softwareAttribution: { attributed: 0, unmatched: 0, ambiguous: 0, unattributable: 1, versionKnown: 0, identitySourceAbsent: false },
  },
  adapterCapabilities: [
    {
      clientId: 'qoder', displayName: 'Qoder', supportLevel: 'MANAGE', declaredOperations: ['read'], matrixOperations: ['read'],
      operationsDrift: false, registryStatus: 'ACTIVE', writePolicy: 'READ_ONLY', risk: 'LOW', runtimeAdapter: null,
      configOwnershipDefault: null, declaredVersion: '1.2.0', versionReadbackMethod: null, versionObservedAt: null,
      versionSource: null, detectionMode: null, detectionEvidenceState: 'REAL', protocolConformance: {},
      observedAt: '2026-10-24T00:00:00Z', layers: [], nativeStatus: 'NOT_PROBED',
      entryProbe: { status: 'PASS', entryPoint: 'qoder', argv: [], exitCode: 0, probedAt: '2026-10-24T00:00:00Z' },
    },
    {
      clientId: 'codex', displayName: 'Codex', supportLevel: 'MANAGE', declaredOperations: [], matrixOperations: [],
      operationsDrift: false, registryStatus: 'ACTIVE', writePolicy: 'READ_ONLY', risk: 'LOW', runtimeAdapter: null,
      configOwnershipDefault: null, declaredVersion: null, versionReadbackMethod: null, versionObservedAt: null,
      versionSource: null, detectionMode: null, detectionEvidenceState: 'NO_EVIDENCE', protocolConformance: {},
      observedAt: null, layers: [], nativeStatus: 'NOT_PROBED', entryProbe: null,
    },
  ],
} as never

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>()
  return { ...actual, useLiveSnapshot: () => ({ snap: mockSnap, source: 'live', live: true, error: null, dataUpdatedAt: 0 }) }
})

vi.mock('@/lib/repairPack', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/repairPack')>()
  return {
    ...actual,
    makeHttpRepairPackReader: () => async () => ({
      kind: 'RESULT',
      httpStatus: 200,
      endpoint: 'test',
      view: {
        schemaVersion: 'worklab/repair-packs-view/v1', status: 'OK', reason: '测试', generatedAt: '2026-10-24T00:00:00Z',
        issuesSummary: null,
        packs: [{
          schemaVersion: 'worklab/repair-pack/v1', packId: 'pack-1', generatedAt: '2026-10-24T00:00:00Z',
          status: 'DRAFT', readiness: { state: 'READY', reasons: [] },
          target: { kind: 'project', projectId: 'proj-a', projectName: '示例项目甲', projectRoot: '/tmp', adapter: null, declaredOperations: [], operation: 'fix', routingSource: 'test' },
          binds: { issueFingerprints: ['fp-aaa'], evidenceRefs: [], classes: [], priorities: [], issueCount: 1, softwareIds: [], unattributedCount: 0 },
          verification: { known: false, command: '', basis: '' },
          handoff: { mode: 'manual_copy', copyable: true, sent: false, dispatched: false, requiresOwnerAction: '' },
          handoffText: '后端渲染的交接文本（PACK-1）',
        }],
        summary: { openIssueCount: 1, packCount: 1 },
      },
    }),
  }
})

const solutionA = {
  solutionId: 'sol-a', revision: 3, title: '方法甲：检查更新后的构建产物', status: 'VALIDATED', recommended: true,
  software: { softwareId: 'work-lab' }, versionHint: { state: 'SAME', message: '记录版本一致' },
  limits: ['仅适用于本机构建链'], steps: ['步骤甲一', '步骤甲二'], verificationSteps: ['验证甲'],
  preconditions: ['前提甲'], risks: [], invalidWhen: ['构建脚本变更后失效'],
  issueRefs: [], evidenceRefs: [], source: {}, score: 5, matchedTerms: [], issueMatch: false,
}
const solutionB = {
  solutionId: 'sol-b', revision: 1, title: '方法乙：回退到上一个可用版本', status: 'CANDIDATE', recommended: false,
  software: { softwareId: 'design-lab-project' }, versionHint: { state: 'UNKNOWN', message: '无版本记录' },
  limits: [], steps: ['步骤乙一'], verificationSteps: [], preconditions: [], risks: ['会丢弃本地改动'],
  invalidWhen: [], issueRefs: ['fp-aaa'], evidenceRefs: [], source: {}, score: 0, matchedTerms: [], issueMatch: true,
}

vi.mock('@/daily/solutionsClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/daily/solutionsClient')>()
  return {
    ...actual,
    fetchSolutions: async () => ({
      kind: 'RESULT',
      view: {
        schemaVersion: 'worklab/solution-search/v1', status: 'OK', reason: '测试', query: '',
        results: [solutionA, solutionB],
        summary: { mode: 'BROWSE' },
      },
    }),
  }
})

import App from '@/App'
import { HudDaily } from '@/daily/HudDaily'
import { buildHandoverMaterial } from '@/daily/dailyData'

beforeEach(() => {
  window.history.replaceState(null, '', '/index.html?shell=daily')
})
afterEach(() => {
  cleanup()
  window.history.replaceState(null, '', window.location.pathname)
})

describe('日常壳（?shell=daily）', () => {
  it('一级导航只有 项目/问题与经验/我的工具，设置底置（导航末位）', () => {
    render(<App />)
    const nav = screen.getByRole('navigation', { name: '主导航' })
    const buttons = Array.from(nav.querySelectorAll('button')).map((b) => b.textContent)
    expect(buttons).toEqual(['项目', '问题与经验', '我的工具', '设置'])
  })

  it('无数据不补 0：概览页显示待确认/UNKNOWN 而不是编造的百分比', () => {
    window.history.replaceState(null, '', '/index.html?shell=daily&dv=overview&dp=proj-b')
    render(<App />)
    expect(screen.getByText(/最近变化：待确认/)).toBeTruthy()
    expect(screen.queryByText(/%/)).toBeNull()
  })

  it('等待用户决定的状态由真实执行行推出（proj-a 有 WAITING_USER）', () => {
    render(<App />)
    expect(screen.getByText('需要关注')).toBeTruthy()
    expect(screen.getByText('状态待确认')).toBeTruthy()
  })

  it('不同方法打开各自记录：抽屉内容随 methodId 变化', async () => {
    window.history.replaceState(null, '', '/index.html?shell=daily&dv=overview&dp=proj-a')
    render(<App />)
    const openA = (await screen.findAllByText('查看该方法详情 →'))[0]
    await act(async () => { openA.click() })
    expect((await screen.findAllByText('方法甲：检查更新后的构建产物')).length).toBeGreaterThan(0)
    expect(screen.getByText(/步骤甲一/)).toBeTruthy()
    // 切到方法乙：整张抽屉内容替换，不再有甲的步骤
    await act(async () => { screen.getByLabelText('关闭抽屉').click() })
    const homeBtn = screen.getByRole('button', { name: '项目' })
    await act(async () => { homeBtn.click() })
    // 通过搜索直接打开 sol-b：方法抽屉由 URL 驱动，这里直接改地址后重挂
    cleanup()
    window.history.replaceState(null, '', '/index.html?shell=daily&dv=overview&dp=proj-a&dm=sol-b')
    render(<App />)
    expect((await screen.findAllByText('方法乙：回退到上一个可用版本')).length).toBeGreaterThan(0)
    expect(screen.queryByText(/步骤甲一/)).toBeNull()
    expect(screen.getByText(/会丢弃本地改动/)).toBeTruthy()
  })

  it('预览、复制与导出来自同一材料；复制失败给出可选择文本而不是假成功', async () => {
    window.history.replaceState(null, '', '/index.html?shell=daily&dv=overview&dp=proj-a&dm=sol-a')
    render(<App />)
    const preview = await screen.findByLabelText('交接材料预览') as HTMLTextAreaElement
    expect(preview.value).toContain('方法甲：检查更新后的构建产物')
    expect(preview.value).toContain('适用限制')
    // jsdom 没有可用的剪贴板/ execCommand：必须报告失败而不是 Toast 假成功
    const copyBtn = screen.getByRole('button', { name: '复制给外部工具' })
    await act(async () => { copyBtn.click() })
    expect(await screen.findByRole('alert')).toBeTruthy()
    expect(screen.getByRole('alert').textContent).toContain('可手动选择复制')
  })

  it('我的工具：切换工具整个详情同步替换', async () => {
    render(<App />)
    await act(async () => { screen.getByRole('button', { name: '我的工具' }).click() })
    expect((await screen.findAllByText('Qoder')).length).toBeGreaterThan(0)
    expect(screen.getByText('声明操作：read（READ_ONLY）')).toBeTruthy()
    await act(async () => { fireEvent.click(screen.getAllByText('Codex')[0]) })
    expect(screen.getByText('无已声明操作记录')).toBeTruthy()
    expect(screen.getByText('未连接（无入口探测记录）')).toBeTruthy()
    expect(screen.queryByText('声明操作：read（READ_ONLY）')).toBeNull()
  })

  it('反馈是内存态：显示“你反馈”，并明确提示刷新后丢失，不宣称系统已验证', async () => {
    window.history.replaceState(null, '', '/index.html?shell=daily&dv=issues')
    render(<App />)
    const row = await screen.findByRole('button', { name: /示例问题：采集器连续失败/ })
    await act(async () => { row.click() })
    const restored = await screen.findByRole('button', { name: '已恢复' })
    await act(async () => { restored.click() })
    expect(screen.getByText('你反馈：已恢复')).toBeTruthy()
    expect(screen.getByText(/反馈仅保存在本页内存中，刷新后丢失/)).toBeTruthy()
    expect(screen.queryByText(/系统已验证/)).toBeNull()
  })
})

describe('HUD 四态（?hud=daily）', () => {
  it('H01 窄面板：两个工具各自成行，额度一律 UNKNOWN，不出现虚构百分比', () => {
    window.history.replaceState(null, '', '/index.html?layout=compact&hud=daily&hs=h01')
    render(<App />)
    expect(screen.getByText('QO')).toBeTruthy()
    expect(screen.getByText('CO')).toBeTruthy()
    expect(screen.getAllByText('额度 UNKNOWN').length).toBe(2)
    expect(screen.queryByText(/79%|12%/)).toBeNull()
  })

  it('H03 工具详情不画虚构柱状图；H04 提醒不冒充系统确认', () => {
    window.history.replaceState(null, '', '/index.html?layout=compact&hud=daily&hs=h03')
    const { unmount } = render(<App />)
    expect(screen.getByText(/不绘制柱状图/)).toBeTruthy()
    unmount()
    window.history.replaceState(null, '', '/index.html?layout=compact&hud=daily&hs=h04')
    render(<App />)
    expect(screen.getByText(/外部回复不等于系统确认/)).toBeTruthy()
    expect(screen.getByText(/摘要保持 待确认/)).toBeTruthy()
  })

  it('状态切换写回 ?hs=（URL 可分享）', () => {
    window.history.replaceState(null, '', '/index.html?layout=compact&hud=daily')
    render(<App />)
    const btn = screen.getByRole('button', { name: 'H03' })
    btn.click()
    expect(window.location.search).toContain('hs=h03')
  })
})

describe('方法抽屉的修复包材料接口', () => {
  it('方法 issueRefs 对上修复包指纹时，材料用后端 handoffText 并标注来源', async () => {
    window.history.replaceState(null, '', '/index.html?shell=daily&dv=overview&dp=proj-a&dm=sol-b')
    render(<App />)
    const preview = await screen.findByLabelText('交接材料预览') as HTMLTextAreaElement
    expect(preview.value).toContain('后端渲染的交接文本（PACK-1）')
    expect(preview.value).not.toContain('步骤乙一')
    expect(screen.getByText(/来源：修复包 pack-1 · 后端渲染 · 未发送/)).toBeTruthy()
  })

  it('没有对上修复包的方法沿用方案库材料并标注方案来源', async () => {
    window.history.replaceState(null, '', '/index.html?shell=daily&dv=overview&dp=proj-a&dm=sol-a')
    render(<App />)
    const preview = await screen.findByLabelText('交接材料预览') as HTMLTextAreaElement
    expect(preview.value).toContain('方法甲：检查更新后的构建产物')
    expect(screen.getByText(/来源：方案库方法/)).toBeTruthy()
  })
})

describe('交接材料生成器', () => {
  it('pack 材料原样携带后端 handoffText；方法材料含项目/问题/步骤/限制', () => {
    const packMaterial = buildHandoverMaterial({
      projectName: '示例项目甲', issueTitle: null, method: null, pack: {
        schemaVersion: 'worklab/repair-pack/v1', packId: 'pack-1', generatedAt: '2026-10-24T00:00:00Z',
        status: 'DRAFT', readiness: { state: 'READY', reasons: [] },
        target: { kind: 'project', projectId: 'proj-a', projectName: '示例项目甲', projectRoot: '/tmp', adapter: null, declaredOperations: [], operation: 'fix', routingSource: 'test' },
        binds: { issueFingerprints: ['fp'], evidenceRefs: [], classes: [], priorities: [], issueCount: 1, softwareIds: [], unattributedCount: 0 },
        verification: { known: false, command: '', basis: '' },
        handoff: { mode: 'manual_copy', copyable: true, sent: false, dispatched: false, requiresOwnerAction: '' },
        handoffText: '后端渲染的交接文本',
      }, targetTool: 'Qoder',
    })
    expect(packMaterial.text).toContain('后端渲染的交接文本')
    expect(packMaterial.text).toContain('示例项目甲')
    const methodMaterial = buildHandoverMaterial({
      projectName: '示例项目乙', issueTitle: '某问题', method: solutionA as never, pack: null, targetTool: '',
    })
    expect(methodMaterial.text).toContain('项目：示例项目乙')
    expect(methodMaterial.text).toContain('问题：某问题')
    expect(methodMaterial.text).toContain('1. 步骤甲一')
    expect(methodMaterial.text).toContain('适用限制')
  })
})

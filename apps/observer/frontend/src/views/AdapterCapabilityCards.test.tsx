// P1-03 behaviour tests for the Agent capability cards.
//
// The point of these cards is that a reader can tell declaration from observation. So the tests are
// written around the failure they exist to prevent: a card that reads as "installed/native" without
// evidence, and a missing source silently rendering as an empty shelf.
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AdapterCapabilityCards } from '@/views/AdapterCapabilityCards'
import { AgentsView } from '@/views/Views'
import type { AdapterCapabilityCard, SnapshotV3 } from '@/types'

function snapshotWith(cards?: AdapterCapabilityCard[]): SnapshotV3 {
  const s = {} as unknown as SnapshotV3
  s.schemaVersion = 'workflow/snapshot/v3'
  s.revision = 1
  s.generatedAt = '2026-10-08T00:00:00Z'
  s.sourceWatermark = null
  s.transport = { transportState: 'LIVE', freshnessState: 'FRESH', connectedSince: null, eventsUrl: null }
  s.coverage = { numerator: null, denominator: null, scope: null }
  s.governance = { state: 'OK', families: {} } as SnapshotV3['governance']
  s.workspace = {}
  s.projects = []
  s.executions = []
  s.tasks = {}
  s.tokenSummary = { inputTokens: null, outputTokens: null, totalTokens: null, costQuality: 'UNKNOWN' }
  s.git = { localSha: null, remoteSha: null, ciSha: null, matchState: 'UNKNOWN' }
  s.ci = []
  s.sourceRefs = []
  if (cards !== undefined) s.adapterCapabilities = cards
  return s
}

function card(over: Partial<AdapterCapabilityCard> = {}): AdapterCapabilityCard {
  const layers = [
    { layer: 'REGISTERED', state: 'MET', evidenceLevel: 'SYNTHETIC',
      source: 'config/adapter-registry.json#entries[id=hermes]', reason: '登记来自仓库声明文件' },
    { layer: 'INSTALLED', state: 'NOT_PROBED', evidenceLevel: 'NO_EVIDENCE', source: null,
      reason: '软件安装身份投影里没有该客户端的行' },
    { layer: 'LOADED_CONNECTED', state: 'NOT_PROBED', evidenceLevel: 'NO_EVIDENCE', source: null,
      reason: 'adapter 的 invoke/observe 动词仍返回 NOT_IMPLEMENTED' },
    { layer: 'QUALIFIED', state: 'NOT_PROBED', evidenceLevel: 'NO_EVIDENCE', source: null,
      reason: '没有逐能力资格判定' },
    { layer: 'ENABLED_FOR_TASK', state: 'NOT_PROBED', evidenceLevel: 'NO_EVIDENCE', source: null,
      reason: '派发未实现' },
    { layer: 'NATIVE_PROJECTION', state: 'NOT_PROBED', evidenceLevel: 'NO_EVIDENCE', source: null,
      reason: '原生侧状态尚未进入 v3 快照合同' },
    { layer: 'OBSERVED_IN_EXECUTION', state: 'NOT_PROBED', evidenceLevel: 'NO_EVIDENCE', source: null,
      reason: '需要真实执行链上的 receipt/readback' },
  ] as AdapterCapabilityCard['layers']
  return {
    clientId: 'hermes', displayName: 'Hermes', supportLevel: 'deep',
    declaredOperations: ['detect', 'capabilities', 'invoke'],
    matrixOperations: ['detect', 'capabilities', 'invoke'],
    operationsDrift: false,
    registryStatus: 'active', writePolicy: 'approval_required', risk: 'high',
    runtimeAdapter: 'HermesAdapter',
    configOwnershipDefault: { layer: 'USER_OVERLAY', mode: 'MANAGE', preserve_unknown: true },
    clientNote: null,
    declaredVersion: '0.21.5+6948.gedd2476', versionReadbackMethod: 'install-stamp-readback',
    versionObservedAt: '2026-10-07', versionSource: 'install-stamp.json',
    detectionMode: 'isolated', detectionEvidenceState: 'UNVERIFIED',
    protocolConformance: { acp: 'STATIC_PASS', skills: 'STATIC_PASS', mcp: 'STATIC_UNVERIFIED' },
    observedAt: '2026-10-08T00:00:00Z',
    layers,
    nativeStatus: 'NOT_IMPLEMENTED',
    ...over,
  }
}

describe('AdapterCapabilityCards', () => {
  it('a missing field is a source gap, not "no clients"', () => {
    const { container } = render(<AdapterCapabilityCards snap={snapshotWith()} />)
    expect(screen.getByText(/来源缺口/)).toBeTruthy()
    expect(container.textContent).not.toMatch(/没有任何 adapter 条目/)
    expect(screen.getByText(/这里不画一张没有源的卡/)).toBeTruthy()
  })

  it('an empty list is the other statement', () => {
    render(<AdapterCapabilityCards snap={snapshotWith([])} />)
    expect(screen.getByText(/声明源里没有任何 adapter 条目/)).toBeTruthy()
    expect(screen.queryByText(/来源缺口/)).toBeNull()
  })

  it('shows exactly one layer as 成立 and names the gap of the other six', () => {
    const { container } = render(<AdapterCapabilityCards snap={snapshotWith([card()])} />)
    expect(container.textContent).toContain('阶梯 1/7 层成立')
    expect(screen.getAllByText('成立').length).toBe(1)
    expect(screen.getAllByText('未探测').length).toBe(6)
    expect(screen.getByText(/invoke\/observe 动词仍返回 NOT_IMPLEMENTED/)).toBeTruthy()
    expect(screen.getByText(/派发未实现/)).toBeTruthy()
  })

  it('never lets a card read as native: the native status is printed as NOT_IMPLEMENTED', () => {
    render(<AdapterCapabilityCards snap={snapshotWith([card()])} />)
    expect(screen.queryByText(/NATIVELY_VERIFIED/)).toBeNull()
    // NOT_IMPLEMENTED legitimately appears twice: the card's own native status and the layer reason
    expect(screen.getAllByText(/NOT_IMPLEMENTED/).length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText(/声明 ≠ 检测 ≠ 可用 ≠ 调用 ≠ 原生验证/)).toBeTruthy()
  })

  it('carries the detection evidence state without laundering it', () => {
    render(<AdapterCapabilityCards snap={snapshotWith([card()])} />)
    expect(screen.getByText(/isolated \/ UNVERIFIED/)).toBeTruthy()
  })

  it('shows both verb lists and names the drift instead of picking a winner', () => {
    const drifted = card({
      declaredOperations: ['detect', 'capabilities', 'invoke', 'observe'],
      matrixOperations: ['detect', 'capabilities'],
      operationsDrift: true,
    })
    render(<AdapterCapabilityCards snap={snapshotWith([drifted])} />)
    expect(screen.getByText(/不一致：registry 与 capability-matrix/)).toBeTruthy()
    expect(screen.getByText('detect · capabilities')).toBeTruthy()
    expect(screen.getByText('detect · capabilities · invoke · observe')).toBeTruthy()
  })

  it('keeps a legacy-observe client labelled as such', () => {
    render(<AdapterCapabilityCards snap={snapshotWith([card({
      clientId: 'cc-switch', displayName: 'CC Switch', registryStatus: 'legacy_observe',
      writePolicy: 'unavailable', supportLevel: 'deep',
    })])} />)
    expect(screen.getByText('legacy_observe')).toBeTruthy()
    expect(screen.getByText(/writes=unavailable/)).toBeTruthy()
  })

  it('renders no interactive control: the Agents lane stays a projection', () => {
    const { container } = render(<AdapterCapabilityCards snap={snapshotWith([card()])} />)
    expect(container.innerHTML).not.toContain('<button')
    expect(container.innerHTML).not.toContain('<input')
    expect(container.innerHTML).not.toContain('<textarea')
    expect(container.querySelectorAll('a')).toHaveLength(0)
  })

  it('AgentsView keeps its execution table while gaining the cards', () => {
    const s = snapshotWith([card()])
    s.executions = [{
      executionId: 'ex-1', anchorProjectId: 'work-lab', workingArea: '/repo',
      state: 'RUNNING', stateQuality: 'strong', agent: 'hermes', sessionId: 'sess-9', sourceRef: null,
    } as SnapshotV3['executions'][number]]
    render(<AgentsView snap={s} />)
    // 'hermes' legitimately appears twice — the card's clientId and the execution table's agent column
    expect(screen.getAllByText('hermes').length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText('sess-9')).toBeTruthy()
    expect(screen.getByText(/阶梯 1\/7 层成立/)).toBeTruthy()
  })
})

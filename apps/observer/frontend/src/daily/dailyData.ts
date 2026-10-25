// 日常壳（M01–M05）的数据投影：只从真实 v3 快照与既有读取结果派生，
// 缺数据一律 UNKNOWN / 未连接 / 待确认，不补 0、不虚构状态。
import type { SnapshotV3, Project, IssueRecord, AdapterCapabilityCard } from '@/types'
import type { SolutionItem } from '@/daily/solutionsClient'
import type { ManualRepairPack } from '@/lib/repairPack'

// 首页六状态（提示词 §7）：只允许由真实字段推出，推不出就是 状态待确认。
export type ProjectCardStatus =
  | '正在推进' | '需要关注' | '等待你决定' | '已完成' | '暂停' | '状态待确认'

export interface DailyProjectCard {
  projectId: string
  displayName: string
  status: ProjectCardStatus
  latestChange: string | null
  relatedTools: string[]
  updatedAt: string | null
  openIssueCount: number | null
  attentionNote: string | null
}

export function projectCardOf(
  p: Project,
  executions: { executionId: string; state: string }[],
  openIssues: number | null,
): DailyProjectCard {
  const waitingUser = executions.some((e) => e.state === 'WAITING_USER' || e.state === 'WAITING_APPROVAL')
  const blocked = executions.some((e) => e.state === 'BLOCKED' || e.state === 'FAILED')
  let status: ProjectCardStatus
  if (openIssues !== null && openIssues > 0) status = '需要关注'
  else if (waitingUser) status = '等待你决定'
  else if (blocked) status = '需要关注'
  else if (p.activityState === 'ACTIVE') status = '正在推进'
  else if (p.activityState === 'IDLE') status = '暂停'
  else status = '状态待确认'
  return {
    projectId: p.projectId,
    displayName: p.displayName ?? p.projectId,
    status,
    latestChange: p.lastStrongEvidenceAt,
    relatedTools: p.agentPlatform ? [p.agentPlatform] : [],
    updatedAt: p.lastStrongEvidenceAt,
    openIssueCount: openIssues,
    attentionNote: blocked ? '存在 BLOCKED / FAILED 执行记录' : null,
  }
}

export function dailyProjectCards(snap: SnapshotV3 | null, packs: ManualRepairPack[]): DailyProjectCard[] {
  if (!snap) return []
  const openByProject = new Map<string, number>()
  for (const issue of snap.issues ?? []) {
    if (!issue.projectId) continue
    openByProject.set(issue.projectId, (openByProject.get(issue.projectId) ?? 0) + 1)
  }
  for (const pack of packs) {
    // 一个 pack 绑定的 open issue 已由 issue 行计数，这里不重复计数。
    void pack
  }
  return (snap.projects ?? []).map((p) => {
    const own = (snap.executions ?? []).filter((e) => e.anchorProjectId === p.projectId)
    return projectCardOf(p, own, openByProject.has(p.projectId) ? (openByProject.get(p.projectId) as number) : 0)
  })
}

export interface DailyIssueRow {
  fingerprint: string
  title: string
  projectId: string | null
  priority: string
  classLabel: string
  detail: string | null
  lastSeenAt: string | null
  packId: string | null
  hasPack: boolean
}

export function dailyIssueRows(snap: SnapshotV3 | null, packs: ManualRepairPack[]): DailyIssueRow[] {
  if (!snap) return []
  const byFingerprint = new Map<string, ManualRepairPack>()
  for (const pack of packs) {
    for (const fp of pack.binds.issueFingerprints) byFingerprint.set(fp, pack)
  }
  return (snap.issues ?? []).map((issue: IssueRecord) => ({
    fingerprint: issue.fingerprint,
    title: issue.subject ?? issue.fingerprint,
    projectId: issue.projectId ?? null,
    priority: issue.priority,
    classLabel: issue.class,
    detail: issue.detail ?? null,
    lastSeenAt: issue.lastSeenAt ?? null,
    packId: byFingerprint.get(issue.fingerprint)?.packId ?? null,
    hasPack: byFingerprint.has(issue.fingerprint),
  }))
}

export interface DailyToolRow {
  clientId: string
  displayName: string
  connection: string
  capabilitySentence: string
  relatedProjects: string[]
  version: string | null
  observedAt: string | null
  writePolicy: string
  registryStatus: string
  // The operator's declared role for this client (agent runtime, provider router, repository host,
  // design client). UNKNOWN means the matrix declares none — a source gap, never a guess from the name.
  role: string
}

export function dailyToolRows(snap: SnapshotV3 | null): DailyToolRow[] {
  const cards: AdapterCapabilityCard[] = snap?.adapterCapabilities ?? []
  return cards.map((card) => {
    const entry = card.entryProbe ?? null
    const connection = entry
      ? (entry.status === 'PASS' ? '已建立基础连接（入口可执行）'
        : entry.status === 'FAIL' ? '入口探测失败（未连接）'
          : `入口探测 ${entry.status}`)
      : '未连接（无入口探测记录）'
    const declared = card.declaredOperations ?? []
    const capability = declared.length > 0
      ? `声明操作：${declared.join('、')}（${card.writePolicy}）`
      : '无已声明操作记录'
    return {
      clientId: card.clientId,
      displayName: card.displayName || card.clientId,
      connection,
      capabilitySentence: capability,
      relatedProjects: (snap?.projects ?? [])
        .filter((p) => p.agentPlatform && card.displayName
          && p.agentPlatform.toLowerCase().includes(card.clientId.toLowerCase()))
        .map((p) => p.displayName ?? p.projectId),
      version: card.declaredVersion ?? null,
      observedAt: card.observedAt ?? null,
      writePolicy: card.writePolicy,
      registryStatus: card.registryStatus,
      role: card.role ?? 'UNKNOWN',
    }
  })
}

// 交接材料：预览 / 复制 / 导出共用这一处生成（提示词 §9）。
export interface HandoverContext {
  projectName: string | null
  issueTitle: string | null
  method: SolutionItem | null
  pack: ManualRepairPack | null
  targetTool: string
}

export function buildHandoverMaterial(ctx: HandoverContext): { text: string; fileName: string } {
  const lines: string[] = []
  lines.push('WORK-LAB 手动交接材料')
  lines.push(`目标工具：${ctx.targetTool || '未选择'}`)
  if (ctx.pack) {
    // 后端渲染的 pack.handoffText 是唯一材料事实；本函数不重写它。
    lines.push(`项目：${ctx.pack.target.projectName ?? ctx.pack.target.projectId}`)
    lines.push('', ctx.pack.handoffText)
    return { text: lines.join('\n'), fileName: `handover-${ctx.pack.packId}.txt` }
  }
  if (ctx.method) {
    lines.push(`项目：${ctx.projectName ?? '未指定'}`)
    lines.push(`问题：${ctx.issueTitle ?? '未指定'}`)
    lines.push(`方法：${ctx.method.title ?? ctx.method.solutionId}（r${ctx.method.revision ?? '?'}，状态 ${ctx.method.status ?? 'UNKNOWN'}）`)
    if (ctx.method.preconditions.length) lines.push('', '前提：', ...ctx.method.preconditions.map((s) => `- ${s}`))
    if (ctx.method.steps.length) lines.push('', '处理步骤（供外部工具参考）：', ...ctx.method.steps.map((s, i) => `${i + 1}. ${s}`))
    if (ctx.method.verificationSteps.length) lines.push('', '验证：', ...ctx.method.verificationSteps.map((s) => `- ${s}`))
    if (ctx.method.limits.length) lines.push('', '适用限制：', ...ctx.method.limits.map((s) => `- ${s}`))
    if (ctx.method.invalidWhen.length) lines.push('', '失效条件：', ...ctx.method.invalidWhen.map((s) => `- ${s}`))
    lines.push('', `来源：方案库 ${ctx.method.solutionId}；适用性以方案自报为准，执行前需复核。`)
    return { text: lines.join('\n'), fileName: `handover-${ctx.method.solutionId}.txt` }
  }
  lines.push('没有可交接的方法或修复包材料。')
  return { text: lines.join('\n'), fileName: 'handover-empty.txt' }
}

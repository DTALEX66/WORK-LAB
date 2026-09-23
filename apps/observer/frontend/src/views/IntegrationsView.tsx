// UI_VIEWS (20260921): Integrations / MCP lane — the backend snapshot has NO
// integrations[] array. What CAN be honestly projected today:
//   1. governance.families.adapters state (CLEAN/DRIFT/UNKNOWN + drift count)
//   2. the 7-client registry of the WORK-LAB control plane (DOCUMENTATION ONLY —
//      a static factual statement of which clients the control plane governs;
//      NOT a live integration status, no fabricated health).
// Everything else stays UNKNOWN.
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/ui/states'
import type { FamilyState, GovernanceFamily } from '@/types'

// Static documentation of the control plane's governed clients. This is a
// fact about the product, not a live status — deliberately rendered as text.
const GOVERNED_CLIENTS = [
  { id: 'hermes', note: 'Hermes Agent · 工作流/规则/技能/MCP 声明治理' },
  { id: 'codex', note: 'Codex · 规则与代理策略投影' },
  { id: 'dsh', note: 'DSH · 软件身份与更新影响适配（只读）' },
  { id: 'cc-switch', note: 'CC Switch · 路由配置差异（OBSERVE）' },
  { id: 'github', note: 'GitHub · CI / 发布 / 分支治理' },
  { id: 'open-design', note: 'Open Design · 前端任务包协作' },
  { id: 'open-human', note: 'Open Human · 会话/执行联邦观察' },
]

function stateVariant(s: FamilyState): 'success' | 'warning' | 'muted' {
  switch (s) {
    case 'CLEAN': return 'success'
    case 'DRIFT': return 'warning'
    default: return 'muted'
  }
}

export function IntegrationsView({ snap }: { snap: any }) {
  const adapters: GovernanceFamily | undefined = snap?.governance?.families?.adapters

  return (
    <div className="flex flex-col gap-4 overflow-auto p-4">
      <Card>
        <CardHeader>
          <span>集成 / MCP · 适配器族</span>
          <span className="text-[11px] text-muted">
            {adapters && adapters.state !== 'UNKNOWN' ? '携带真实状态' : '无适配器明细'}
          </span>
        </CardHeader>
        <CardContent>
          {!adapters || (adapters.state === 'UNKNOWN' && adapters.drift == null) ? (
            <EmptyState
              title="无集成明细"
              description="当前快照未携带 integrations[] 数组或适配器族明细。Observer 保持 UNKNOWN，不伪造集成健康度。"
            />
          ) : (
            <div className="panel2 p-3 flex items-center justify-between">
              <div>
                <div className="text-xs text-ink">适配器等价状态</div>
                <div className="text-[11px] text-muted">
                  漂移项：<span className="font-mono text-secondary">{adapters.drift ?? '未知'}</span>
                </div>
              </div>
              <Badge variant={stateVariant(adapters.state)}>
                {adapters.state}
              </Badge>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><span>受治理客户端（文档 · 非实时状态）</span></CardHeader>
        <CardContent>
          <div className="flex flex-col gap-2">
            {GOVERNED_CLIENTS.map((c) => (
              <div key={c.id} className="flex items-center justify-between gap-3 border-b border-border/40 py-2 last:border-0">
                <div>
                  <div className="text-xs font-medium text-ink">{c.id}</div>
                  <div className="text-[11px] text-muted">{c.note}</div>
                </div>
                <span className="text-[10px] text-muted">受控（无实时状态投影）</span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[11px] text-muted">
            以上为控制面受治理客户端的静态说明。各客户端的实时集成状态需由集成契约
            （integrations[]）投影后方可呈现，当前快照未携带，保持 UNKNOWN。
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

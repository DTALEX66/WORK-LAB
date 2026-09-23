// UI_VIEWS (20260921): Rules & Policy lane — projects the governance family
// states (rules/skills/memory/adapters) already resolved by the backend.
// Honest discipline: when the snapshot carries no family detail we render an
// EmptyState, never a fabricated "all clean" KPI.
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/ui/states'
import type { FamilyState, GovernanceFamily } from '@/types'

const FAMILY_LABEL: Record<keyof GovernanceFamily extends never ? never : 'rules' | 'skills' | 'memory' | 'adapters', string> = {
  rules: '规则',
  skills: '技能',
  memory: '记忆',
  adapters: '适配器',
}

const FAMILY_KEYS = ['rules', 'skills', 'memory', 'adapters'] as const

function stateVariant(s: FamilyState): 'success' | 'warning' | 'muted' {
  switch (s) {
    case 'CLEAN': return 'success'
    case 'DRIFT': return 'warning'
    default: return 'muted'
  }
}

function stateLabel(s: FamilyState): string {
  switch (s) {
    case 'CLEAN': return '干净'
    case 'DRIFT': return '漂移'
    default: return '未知'
  }
}

function hasFamilyData(f: GovernanceFamily): boolean {
  return f.state !== 'UNKNOWN' || f.drift != null || f.current != null
}

export function RulesPolicyView({ snap }: { snap: any }) {
  const families = snap?.governance?.families as
    | Record<string, GovernanceFamily>
    | undefined
  const hasAny =
    !!families && FAMILY_KEYS.some((k) => hasFamilyData(families?.[k]))

  return (
    <div className="flex flex-col gap-4 overflow-auto p-4">
      <Card>
        <CardHeader>
          <span>治理契约 · 家族状态（只读投影）</span>
          <span className="text-[11px] text-muted">
            {hasAny ? '携带真实明细' : '无明细（UNKNOWN）'}
          </span>
        </CardHeader>
        <CardContent>
          {!hasAny ? (
            <EmptyState
              title="当前快照未携带治理契约明细"
              description="governance.families 未由后端投影，或全部为 UNKNOWN。Observer 保持 UNKNOWN，不伪造『全部干净』。"
            />
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {FAMILY_KEYS.map((key) => {
                const fam = families?.[key]
                if (!fam) return null
                return (
                  <div key={key} className="panel2 p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs font-medium text-ink">{FAMILY_LABEL[key]}</span>
                      <Badge variant={stateVariant(fam.state)}>
                        {stateLabel(fam.state)}
                      </Badge>
                    </div>
                    <div className="text-[11px] text-muted">
                      漂移项：
                      <span className="font-mono text-secondary">
                        {fam.drift == null ? '未知' : fam.drift}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><span>原则</span></CardHeader>
        <CardContent className="text-xs text-muted">
          规则 / 技能 / 记忆 / 适配器的真值来自后端治理契约（governance.families）。
          Observer 仅投影状态，不修改、不新增、不执行任何治理动作。
        </CardContent>
      </Card>
    </div>
  )
}

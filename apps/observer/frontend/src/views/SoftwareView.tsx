// S31/S32 (taskpack 20260919): read-only software installation-identity panel.
//
// The Observer projects the software-installation-identity contract (U17/P0-07)
// already resolved by the sidecar/DHS adapter. It NEVER acts on it (no second
// Update Authority, no relocation, no delete). When DSH has drifted to C: or a
// duplicate install exists, this panel shows LOCATION_DRIFT / DUAL_INSTALLATION
// — NOT "Healthy".
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { SoftwareIdentity, SoftwareLocationStatus } from '@/types'

const STATUS_LABEL: Record<SoftwareLocationStatus, string> = {
  NOT_INSTALLED: '未安装',
  SINGLE_VERIFIED: '单一·已验证',
  SINGLE_UNVERIFIED: '单一·未验证',
  LOCATION_DRIFT: '位置漂移',
  DUAL_INSTALLATION: '双安装',
  MISSING_EXPECTED_INSTALL: '预期安装缺失',
  RELOCATION_REQUESTED: '请求迁移',
  OS_MANAGED: '系统托管',
  UNKNOWN: '未知',
}

function statusVariant(s: SoftwareLocationStatus): 'success' | 'warning' | 'error' | 'muted' {
  switch (s) {
    case 'SINGLE_VERIFIED': return 'success'
    case 'SINGLE_UNVERIFIED':
    case 'OS_MANAGED':
    case 'RELOCATION_REQUESTED':
    case 'NOT_INSTALLED':
      return 'muted'
    case 'LOCATION_DRIFT':
    case 'DUAL_INSTALLATION':
    case 'MISSING_EXPECTED_INSTALL':
      return 'error'
    default:
      return 'muted'
  }
}

function Row({ k, v, mono = false }: { k: string; v: React.ReactNode; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between py-1 border-b border-border/40 last:border-0">
      <span className="text-[11px] text-zinc-500">{k}</span>
      <span className={'text-[11px] text-zinc-200 truncate ml-3 text-right' + (mono ? ' font-mono' : '')}>{v}</span>
    </div>
  )
}

export function SoftwareView({ snap }: { snap: any }) {
  const software: SoftwareIdentity[] = Array.isArray(snap?.software) ? snap.software : []
  return (
    <div className="flex flex-col gap-4 overflow-auto p-4">
      <Card>
        <CardHeader>
          <span>软件安装身份（只读投影）</span>
          <span className="text-[11px] text-zinc-500">
            {software.length ? software.length + ' 项 · 真实' : '无数据（UNKNOWN）'}
          </span>
        </CardHeader>
        <CardContent>
          {software.length === 0 ? (
            <div className="text-xs text-zinc-600 py-6 text-center">
              无软件身份投影（后端未提供 · 保持 UNKNOWN，不伪造 Healthy）
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {software.map((s) => (
                <div key={s.softwareId} className="panel2 p-3 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium">{s.displayName || s.softwareId}</span>
                    <Badge variant={statusVariant(s.locationStatus)}>
                      {STATUS_LABEL[s.locationStatus] || s.locationStatus}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px]">
                    <Row k="安装位置" v={s.installRoot || 'UNKNOWN'} mono />
                    <Row k="可执行" v={s.executableRealpath || 'UNKNOWN'} mono />
                    <Row k="发现版本" v={s.discoveredVersion || 'UNKNOWN'} mono />
                    <Row k="渠道" v={s.releaseChannel || 'UNKNOWN'} />
                    <Row k="更新可用" v={s.updateAvailable == null ? 'UNKNOWN' : s.updateAvailable ? '是' : '否'} />
                    <Row k="双安装" v={s.duplicateInstallation ? '是' : '否'} />
                    <Row k="预期位置" v={s.expectedLocation || '—'} mono />
                    <Row k="观测位置" v={s.observedLocation || '—'} mono />
                    <Row k="最后核验" v={s.lastVerified ? new Date(s.lastVerified).toLocaleString() : 'UNKNOWN'} />
                    <Row k="发现源" v={s.discoverySource || '—'} />
                  </div>
                  {s.locationStatus === 'LOCATION_DRIFT' && s.expectedLocation && s.observedLocation && (
                    <div className="mt-2 text-[10px] text-error">
                      漂移：预期 <span className="font-mono">{s.expectedLocation}</span> · 观测
                      <span className="font-mono"> {s.observedLocation}</span> — 需明确 RELOCATION 授权，
                      Observer 不自动迁移
                    </div>
                  )}
                  {s.locationStatus === 'DUAL_INSTALLATION' && (
                    <div className="mt-2 text-[10px] text-error">
                      检测到多实例 — 先确定 canonical 实例；Observer 不自动删除任何实例
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><span>原则</span></CardHeader>
        <CardContent className="text-xs text-zinc-500">
          软件位置真值来自后端安装身份契约（U17/P0-07）。Observer 仅投影，绝不构成第二
          Update Authority；位置漂移/双安装如实呈现，不伪装 Healthy。
        </CardContent>
      </Card>
    </div>
  )
}

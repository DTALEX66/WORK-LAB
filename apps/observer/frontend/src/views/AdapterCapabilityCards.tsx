// P1-03 · Agent 原生能力卡（read-only projection）。
//
// 一张卡讲一件事：这个客户端被**声明**了什么、被**探测**到什么、还**没有**什么。
// 七层阶梯（Registered → Installed → Loaded/Connected → Qualified → Enabled for Task →
// Native Projection → Observed in Execution）各层独立成立，任何一层都不许因为邻层成功而晋级：
// MET 必须带来源，NOT_PROBED 必须带缺什么。这既是合同（snapshot_validator 拒绝无来源的 MET、
// 拒绝在 OBSERVED_IN_EXECUTION 未 MET 时自称 NATIVELY_VERIFIED），也是这里的渲染规则。
//
// 本组件零交互控件：它不代跑探测、不启用能力、不发起会话（Observer §8 只读法）。
import * as React from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { AdapterCapabilityCard, CapabilityLayerState, SnapshotV3 } from '@/types'

type Snap = SnapshotV3 | null

const LAYER_LABEL: Record<string, string> = {
  REGISTERED: '已登记',
  INSTALLED: '已安装',
  LOADED_CONNECTED: '已加载·已连接',
  QUALIFIED: '已资格判定',
  ENABLED_FOR_TASK: '已按任务启用',
  NATIVE_PROJECTION: '原生投影',
  OBSERVED_IN_EXECUTION: '执行中观察',
}

const STATE_TEXT: Record<string, string> = {
  MET: '成立',
  NOT_PROBED: '未探测',
  NOT_SUPPORTED: '不支持',
}

function layerVariant(state: string): 'success' | 'warning' | 'muted' {
  if (state === 'MET') return 'success'
  if (state === 'NOT_SUPPORTED') return 'warning'
  return 'muted'
}

function LayerRow({ layer }: { layer: CapabilityLayerState }) {
  const evidence = layer.state === 'MET'
    ? `${layer.evidenceLevel} · 来源 ${layer.source || 'UNKNOWN'}`
    : `${layer.evidenceLevel} · ${layer.reason}`
  return (
    <div className="list-item flex-col items-stretch gap-1">
      <div className="flex items-center gap-2">
        <span className="text-[11px] text-ink">{LAYER_LABEL[layer.layer] || layer.layer}</span>
        <Badge variant={layerVariant(layer.state)}>{STATE_TEXT[layer.state] || layer.state}</Badge>
      </div>
      <div className="break-words text-[10px] text-muted">{evidence}</div>
    </div>
  )
}

function Fact({ label, value }: { label: string, value: React.ReactNode }) {
  const present = value !== null && value !== undefined && value !== '' && value !== false
  return (
    <div className="list-item flex-col items-stretch gap-1">
      <div className="text-[10px] uppercase tracking-[0.12em] text-muted">{label}</div>
      <div className="break-words text-[11px] text-ink">{present ? value : 'UNKNOWN'}</div>
    </div>
  )
}

function AdapterCard({ card }: { card: AdapterCapabilityCard }) {
  const observed = card.layers.filter((layer) => layer.state === 'MET').length
  return (
    <Card>
      <CardHeader>
        <span>{card.displayName} · <span className="font-mono text-[11px]">{card.clientId}</span></span>
        <span className="flex flex-wrap items-center gap-1.5 text-[10px] text-muted">
          <Badge variant={card.supportLevel === 'deep' ? 'info' : 'muted'}>{card.supportLevel}</Badge>
          <Badge variant={card.registryStatus === 'active' ? 'success' : 'warning'}>
            {card.registryStatus}
          </Badge>
          阶梯 {observed}/{card.layers.length} 层成立
        </span>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="text-[10px] text-muted">
          声明 ≠ 检测 ≠ 可用 ≠ 调用 ≠ 原生验证；原生状态：
          <span className="ml-1 font-mono">{card.nativeStatus}</span>
        </div>

        <div className="list">
          {card.layers.map((layer) => <LayerRow key={layer.layer} layer={layer} />)}
        </div>

        <div className="list">
          <Fact label="版本（读回）"
            value={card.declaredVersion
              ? `${card.declaredVersion} · ${card.versionReadbackMethod || 'UNKNOWN'} · ${card.versionObservedAt || 'UNKNOWN'}`
              : null} />
          <Fact label="检测证据态"
            value={`${card.detectionMode || 'UNKNOWN'} / ${card.detectionEvidenceState}`} />
          <Fact label="声明动词（registry）"
            value={card.declaredOperations.length ? card.declaredOperations.join(' · ') : null} />
          <Fact label="动词清单（capability-matrix）"
            value={card.matrixOperations.length ? card.matrixOperations.join(' · ') : null} />
          <Fact label="两份声明是否一致"
            value={card.operationsDrift
              ? '不一致：registry 与 capability-matrix 列出的动词集合不同，两处都原样展示，不替你做选择'
              : (card.matrixOperations.length ? '一致' : null)} />
          <Fact label="写策略 / 风险"
            value={`writes=${card.writePolicy} · risk=${card.risk}`} />
          <Fact label="配置归属默认"
            value={card.configOwnershipDefault
              ? `${card.configOwnershipDefault.layer || 'UNKNOWN'} / ${card.configOwnershipDefault.mode || 'UNKNOWN'} / preserve_unknown=${String(card.configOwnershipDefault.preserve_unknown ?? 'UNKNOWN')}`
              : null} />
          <Fact label="运行时适配器" value={card.runtimeAdapter} />
          <Fact label="协议符合性"
            value={Object.entries(card.protocolConformance)
              .map(([protocol, status]) => `${protocol}=${status}`).join(' · ')} />
          <Fact label="备注" value={card.clientNote} />
          <Fact label="投影时间" value={card.observedAt} />
        </div>
      </CardContent>
    </Card>
  )
}

export function AdapterCapabilityCards({ snap }: { snap: Snap }) {
  const cards = snap?.adapterCapabilities
  if (cards === undefined) {
    return (
      <Card>
        <CardHeader><span>原生能力卡</span></CardHeader>
        <CardContent>
          <div className="text-xs text-warning">
            来源缺口：快照没有 adapterCapabilities 字段 —— 生产者未能读取
            config/adapter-registry.json / capability-matrix.json / capability-conformance.json。
            这里不画一张没有源的卡，也不把“读不到”说成“没有客户端”。
          </div>
        </CardContent>
      </Card>
    )
  }
  if (!cards.length) {
    return (
      <Card>
        <CardHeader><span>原生能力卡</span></CardHeader>
        <CardContent>
          <div className="text-xs text-muted">
            声明源里没有任何 adapter 条目（已读取文件，结果为空）。
          </div>
        </CardContent>
      </Card>
    )
  }
  return (
    <>
      {cards.map((card) => <AdapterCard key={card.clientId} card={card} />)}
    </>
  )
}

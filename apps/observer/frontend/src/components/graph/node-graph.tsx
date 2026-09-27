// L10 (2026-09-27): B10 `.graph-stage` observer topology — read-only SVG
// radial graph: a pulsing core + satellite nodes with cyan halos. This is
// the Observer §8 read-only projection surface: clicking a node reports it
// via onSelect (the parent opens a Drawer); there are NO write controls.
// Geometry: core at 50/50, satellites on a ring (B10 `.graph-stage` coords).
import * as React from 'react'
import { cn } from '@/lib/utils'

export interface GraphNode {
  id: string
  label: string
  /** node runtime truth: running/active node gets the pulse halo */
  state?: 'active' | 'idle' | 'error' | 'unknown'
}

export interface GraphEdge {
  from: string
  to: string
}

export interface NodeGraphProps {
  core: string
  nodes: GraphNode[]
  edges?: GraphEdge[]
  /** 0..100 viewBox is 100x100; satellite ring radius defaults to 34 */
  className?: string
  onSelect?: (id: string | null) => void
  selected?: string | null
}

const RING = [
  [50, 14], [82, 28], [86, 68], [52, 86], [16, 68], [18, 28],
]

function stateClass(n: GraphNode): string {
  switch (n.state) {
    case 'active': return 'text-secondary'
    case 'error': return 'text-error'
    default: return 'text-muted'
  }
}

export function NodeGraph({ core, nodes, edges, className, onSelect, selected }: NodeGraphProps) {
  const shown = nodes.slice(0, 6)
  return (
    <div
      className={cn(
        'graph-stage relative min-h-[320px] rounded-lg border border-border/58 overflow-hidden',
        className,
      )}
    >
      <svg
        viewBox="0 0 100 100"
        className="h-full w-full"
        role="img"
        aria-label={`观察者拓扑：${core} 及 ${shown.length} 个节点`}
      >
        {(edges ?? shown.map((n, i) => ({ from: '__core__', to: n.id }))).map((e, i) => {
          const a = e.from === '__core__' || e.from === core ? [50, 50] : RING[shown.findIndex((n) => n.id === e.from)] ?? [50, 50]
          const b = e.to === '__core__' || e.to === core ? [50, 50] : RING[shown.findIndex((n) => n.id === e.to)] ?? [50, 50]
          return <line key={i} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke="var(--color-border)" strokeWidth="0.6" opacity={0.8} />
        })}
        {/* core — the pulsing halo (B10 .core) */}
        <circle cx={50} cy={50} r={8} fill="rgb(var(--primary-rgb))" className="wl-core-pulse" style={{ filter: 'drop-shadow(0 0 18px color-mix(in srgb, rgb(var(--primary-rgb)) 48%, transparent))' }} />
        <text x={50} y={52} textAnchor="middle" fontSize="5" fill="#fff" fontWeight={700}>{core}</text>
        {shown.map((n, i) => {
          const [cx, cy] = RING[i]
          const isSel = selected === n.id
          return (
            <g key={n.id} className="cursor-pointer" onClick={() => onSelect?.(isSel ? null : n.id)}>
              <circle
                cx={cx}
                cy={cy}
                r={isSel ? 5.6 : 4.6}
                fill="color-mix(in srgb, var(--color-panel2) 88%, transparent)"
                stroke={isSel ? 'rgb(var(--secondary-rgb))' : n.state === 'error' ? 'rgb(var(--error-rgb))' : 'color-mix(in srgb, rgb(var(--secondary-rgb)) 65%, white 2%)'}
                strokeWidth={isSel ? 1.4 : 0.9}
                style={{ filter: 'drop-shadow(0 0 8px color-mix(in srgb, rgb(var(--primary-rgb)) 18%, transparent))' }}
              />
              <text x={cx} y={cy + 1.4} textAnchor="middle" fontSize="3.8" fill="var(--color-ink)" className={stateClass(n)}>
                {n.label}
              </text>
              {n.state === 'active' ? (
                <circle cx={cx + 6.4} cy={cy - 4.2} r={1.2} fill="rgb(var(--success-rgb))" className="wl-core-pulse" />
              ) : null}
              {n.state === 'error' ? (
                <circle cx={cx + 6.4} cy={cy - 4.2} r={1.2} fill="rgb(var(--error-rgb))" />
              ) : null}
            </g>
          )
        })}
      </svg>
    </div>
  )
}

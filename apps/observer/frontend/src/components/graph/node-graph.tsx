// L10 (2026-09-27) · L10b: B10 `.graph-stage` observer topology — read-only SVG
// radial graph: a pulsing core + satellite nodes with cyan halos.
//
// The DOM is the verbatim B10 structure:
//   <div class="graph-stage">
//     <svg viewBox="0 0 100 100">
//       <line stroke="var(--border)">…connectors…
//       <circle class="core" cx=50 cy=50 r=8/>
//       <text …>Core</text>
//       <circle class="node-dot" …/><text …>label</text> × 6
//     </svg>
//   </div>
// `.graph-stage`, `circle.node-dot`, `.core` (primary pulse) are B10-verbatim in
// src/skins/b10.css, so the satellite circles now inherit the B10 fill, cyan
// stroke and hover halo directly instead of inline styles.
//
// This is the Observer §8 read-only projection surface: clicking a node reports
// it via onSelect (the parent opens a Drawer); there are NO write controls.
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
  /** 0..100 viewBox is 100x100; satellites sit on the B10 ring */
  className?: string
  onSelect?: (id: string | null) => void
  selected?: string | null
}

const RING = [
  [50, 14], [82, 28], [86, 68], [52, 86], [16, 68], [18, 28],
]

const STATE_FILL: Record<string, string> = {
  active: 'rgb(var(--secondary-rgb))',
  error: 'rgb(var(--error-rgb))',
  idle: 'var(--text)',
  unknown: 'var(--muted)',
}

export function NodeGraph({ core, nodes, edges, className, onSelect, selected }: NodeGraphProps) {
  const shown = nodes.slice(0, 6)
  return (
    <div className={cn('graph-stage', className)}>
      <svg
        viewBox="0 0 100 100"
        role="img"
        aria-label={`观察者拓扑：${core} 及 ${shown.length} 个节点`}
      >
        {(edges ?? shown.map((n) => ({ from: '__core__', to: n.id }))).map((e, i) => {
          const a = e.from === '__core__' || e.from === core ? [50, 50] : RING[shown.findIndex((n) => n.id === e.from)] ?? [50, 50]
          const b = e.to === '__core__' || e.to === core ? [50, 50] : RING[shown.findIndex((n) => n.id === e.to)] ?? [50, 50]
          return <line key={i} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke="var(--border)" strokeWidth="0.6" opacity={0.8} />
        })}
        {/* core — the B10 pulsing halo */}
        <circle className="core" cx={50} cy={50} r={8} />
        <text x={50} y={52} textAnchor="middle" fontSize="5" fill="#fff" fontWeight={700}>{core}</text>
        {shown.map((n, i) => {
          const [cx, cy] = RING[i]
          const isSel = selected === n.id
          // Label anchor: B10 prints the satellite name at the ring centre with
          // a 3.8px glyph. At the real container size that overlaps the dot, so
          // the label is kept on the SAME node-dot ring but placed just OUTSIDE
          // the circle along the radial direction (readable, still B10-styled).
          const labelY = cy < 50 ? cy - 8 : cy + 10.5
          return (
            <g
              key={n.id}
              className="cursor-pointer"
              onClick={() => onSelect?.(isSel ? null : n.id)}
              // Satellite state was carried by fill colour alone (active / error
              // / idle / unknown), so it was invisible to colour-blind users and
              // to screen readers, and the node could not be reached by keyboard.
              role="button"
              tabIndex={0}
              aria-label={`${n.label} · ${n.state}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onSelect?.(isSel ? null : n.id)
                }
              }}
            >
              <circle
                className={cn('node-dot', isSel && 'active')}
                cx={cx}
                cy={cy}
                r={isSel ? 5.6 : 5}
              />
              <text
                x={cx}
                y={labelY}
                textAnchor="middle"
                fontSize="5"
                fill={STATE_FILL[n.state ?? 'idle']}
              >
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

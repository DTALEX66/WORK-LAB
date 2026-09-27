// L10 (2026-09-27): B10 workflow editor canvas — an INTERACTIVE node surface
// (NOT a static flow diagram). Drag nodes, zoom, pan, select, connect,
// delete, with a B10 `.node` look (16px radius, primary border + glow) and
// `.flow-svg` animated dashed edges. Node positions + edges live in the
// caller's state (local model; persisted via localStorage by the view).
//
// Honest boundary: this canvas is a LOCAL editing model. "发布 / 运行" is the
// caller's contract — until a real workflow-schema backend is wired the view
// renders those actions disabled + explanatory (no fake success), but the
// canvas interaction (drag/select/connect/delete/zoom) is fully real.
import * as React from 'react'
import { ZoomIn, ZoomOut, Maximize, Plus, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'

export type NodeKind =
  | 'Trigger' | 'Validate' | 'Agent' | 'Tool' | 'Approval'
  | 'Condition' | 'Deploy' | 'Output'

export interface FlowNode {
  id: string
  kind: NodeKind
  label: string
  meta?: string
  x: number
  y: number
}

export interface FlowEdge {
  id: string
  from: string
  to: string
}

export const NODE_KINDS: NodeKind[] = [
  'Trigger', 'Validate', 'Agent', 'Tool', 'Approval', 'Condition', 'Deploy', 'Output',
]

const NODE_W = 150
const NODE_H = 64
const KIND_COLOR: Record<NodeKind, string> = {
  Trigger: 'rgb(var(--secondary-rgb))',
  Validate: 'rgb(var(--primary-rgb))',
  Agent: 'rgb(var(--primary-rgb))',
  Tool: 'rgb(var(--secondary-rgb))',
  Approval: 'rgb(var(--warning-rgb))',
  Condition: 'rgb(var(--info-rgb))',
  Deploy: 'rgb(var(--success-rgb))',
  Output: 'rgb(var(--secondary-rgb))',
}

export interface WorkflowCanvasProps {
  nodes: FlowNode[]
  edges: FlowEdge[]
  onNodesChange: (n: FlowNode[]) => void
  onEdgesChange: (e: FlowEdge[]) => void
  /** add a node of a given kind at a fresh position */
  onAddNode?: (kind: NodeKind) => void
  onPublish?: () => void
  onRun?: () => void
  publishDisabled?: boolean
  runDisabled?: boolean
  publishHint?: string
  runHint?: string
  /** selected node id drives the property panel */
  selectedId?: string | null
  onSelect?: (id: string | null) => void
}

export function WorkflowCanvas({
  nodes, edges, onNodesChange, onEdgesChange,
  onAddNode, onPublish, onRun,
  publishDisabled, runDisabled, publishHint, runHint,
  selectedId, onSelect,
}: WorkflowCanvasProps) {
  const [zoom, setZoom] = React.useState(1)
  const [pan, setPan] = React.useState({ x: 0, y: 0 })
  const [dragId, setDragId] = React.useState<string | null>(null)
  const [connecting, setConnecting] = React.useState<{ from: string; x: number; y: number } | null>(null)
  const canvasRef = React.useRef<HTMLDivElement>(null)
  const [canvasSize, setCanvasSize] = React.useState({ w: 800, h: 520 })

  // measure the canvas for edge geometry
  React.useEffect(() => {
    const el = canvasRef.current
    if (!el) return
    const ro = new ResizeObserver(() => setCanvasSize({ w: el.clientWidth, h: el.clientHeight }))
    ro.observe(el)
    setCanvasSize({ w: el.clientWidth, h: el.clientHeight })
    return () => ro.disconnect()
  }, [])

  const nodeById = React.useMemo(() => {
    const m = new Map<string, FlowNode>()
    for (const n of nodes) m.set(n.id, n)
    return m
  }, [nodes])

  // ---- node dragging (pointer) ----
  const onPointerMove = (e: React.PointerEvent) => {
    if (!dragId && !connecting) return
    const canvas = canvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    const px = (e.clientX - rect.left) / zoom
    const py = (e.clientY - rect.top) / zoom
    if (dragId) {
      onNodesChange(nodes.map((n) => (n.id === dragId ? { ...n, x: px - NODE_W / 2, y: py - NODE_H / 2 } : n)))
    } else if (connecting) {
      setConnecting({ ...connecting, x: px, y: py })
    }
  }

  const onPointerUp = () => {
    if (connecting && canvasRef.current) {
      // drop on a node completes a connection
      const canvas = canvasRef.current
      const el = document.elementFromPoint(
        (connecting.x * zoom + pan.x) + canvas.offsetLeft,
        (connecting.y * zoom + pan.y) + canvas.offsetTop,
      )
      const target = el?.closest?.('[data-node-id]') as HTMLElement | null
      if (target) {
        const tid = target.dataset.nodeId
        if (tid && tid !== connecting.from) {
          onEdgesChange([...edges, { id: `e-${connecting.from}-${tid}`, from: connecting.from, to: tid }])
        }
      }
      setConnecting(null)
    }
    setDragId(null)
  }

  const startDrag = (e: React.PointerEvent, id: string) => {
    e.stopPropagation()
    ;(e.target as Element).setPointerCapture?.(e.pointerId)
    setDragId(id)
    onSelect?.(id)
  }

  const startConnect = (e: React.PointerEvent, from: string) => {
    e.stopPropagation()
    ;(e.target as Element).setPointerCapture?.(e.pointerId)
    const canvas = canvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    setConnecting({ from, x: (e.clientX - rect.left) / zoom, y: (e.clientY - rect.top) / zoom })
  }

  // ---- pan (background drag) ----
  const panStart = React.useRef<{ x: number; y: number; panX: number; panY: number } | null>(null)
  const onBgPointerDown = (e: React.PointerEvent) => {
    if (e.target !== canvasRef.current) return
    ;(e.target as Element).setPointerCapture?.(e.pointerId)
    panStart.current = { x: e.clientX, y: e.clientY, panX: pan.x, panY: pan.y }
  }
  const onBgPointerMove = (e: React.PointerEvent) => {
    if (!panStart.current) return
    setPan({ x: panStart.current.panX + (e.clientX - panStart.current.x), y: panStart.current.panY + (e.clientY - panStart.current.y) })
  }
  const onBgPointerUp = () => { panStart.current = null }

  const deleteSelected = () => {
    if (!selectedId) return
    onNodesChange(nodes.filter((n) => n.id !== selectedId))
    onEdgesChange(edges.filter((e) => e.from !== selectedId && e.to !== selectedId))
    onSelect?.(null)
  }

  const nodeCenter = (n: FlowNode) => ({ x: n.x + NODE_W / 2, y: n.y + NODE_H / 2 })
  const edgePath = (a: FlowNode, b: FlowNode) => {
    const p = nodeCenter(a), q = nodeCenter(b)
    const mx = (p.x + q.x) / 2
    return `M ${p.x} ${p.y} C ${mx} ${p.y}, ${mx} ${q.y}, ${q.x} ${q.y}`
  }

  return (
    <div className="flex flex-col gap-3">
      {/* toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1 rounded-lg border border-border bg-panel2/72 px-2 py-1.5">
          {NODE_KINDS.map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => onAddNode?.(k)}
              title={`添加 ${k} 节点`}
              aria-label={`添加 ${k} 节点`}
              className="flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-ink hover:bg-panel2 transition-colors duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <span className="h-2 w-2 rounded-full" style={{ background: KIND_COLOR[k] }} aria-hidden />
              {k}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1 ml-auto">
          <button type="button" onClick={() => setZoom((z) => Math.max(0.4, z - 0.1))} aria-label="缩小" className="rounded-md border border-border bg-panel2/72 p-1.5 text-muted hover:text-ink"><ZoomOut size={14} /></button>
          <button type="button" onClick={() => setZoom(1)} aria-label="适应画布" title="重置缩放与平移" className="rounded-md border border-border bg-panel2/72 p-1.5 text-muted hover:text-ink"><Maximize size={14} /></button>
          <button type="button" onClick={() => setZoom((z) => Math.min(2.4, z + 0.1))} aria-label="放大" className="rounded-md border border-border bg-panel2/72 p-1.5 text-muted hover:text-ink"><ZoomIn size={14} /></button>
          <button type="button" onClick={deleteSelected} disabled={!selectedId} aria-label="删除所选节点" title="删除所选节点" className="rounded-md border border-border bg-panel2/72 p-1.5 text-muted hover:text-error disabled:opacity-40"><Trash2 size={14} /></button>
        </div>
      </div>

      {/* canvas */}
      <div
        ref={canvasRef}
        className="wl-canvas relative h-[520px] overflow-hidden rounded-lg border border-border/60"
        style={{
          background: [
            'linear-gradient(var(--grid-line) 1px, transparent 1px)',
            'linear-gradient(90deg, var(--grid-line) 1px, transparent 1px)',
            'radial-gradient(circle at 30% 20%, color-mix(in srgb, rgb(var(--primary-rgb)) 8%, transparent), transparent 40%)',
          ].join(','),
          backgroundSize: '30px 30px, 30px 30px, auto',
          cursor: panStart.current ? 'grabbing' : 'default',
        }}
        onPointerDown={onBgPointerDown}
        onPointerMove={(e) => { onBgPointerMove(e); onPointerMove(e) }}
        onPointerUp={(e) => { onBgPointerUp(); onPointerUp() }}
        onPointerLeave={() => { onBgPointerUp(); onPointerUp() }}
      >
        <div
          className="absolute inset-0"
          style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: '0 0' }}
        >
          <svg className="pointer-events-none absolute inset-0 h-full w-full overflow-visible" style={{ width: '100%', height: '100%' }}>
            {edges.map((e) => {
              const a = nodeById.get(e.from), b = nodeById.get(e.to)
              if (!a || !b) return null
              return <path key={e.id} d={edgePath(a, b)} className="wl-edge-line" />
            })}
            {connecting ? (
              <line x1={nodeById.get(connecting.from) ? nodeCenter(nodeById.get(connecting.from)!).x : 0} y1={nodeById.get(connecting.from) ? nodeCenter(nodeById.get(connecting.from)!).y : 0} x2={connecting.x} y2={connecting.y} className="wl-edge-line" />
            ) : null}
          </svg>
          {nodes.map((n) => {
            const sel = selectedId === n.id
            return (
              <div
                key={n.id}
                data-node-id={n.id}
                className={cn(
                  'wl-node absolute select-none rounded-lg border p-3',
                  sel ? 'wl-node-active' : 'wl-node-glow',
                )}
                style={{
                  left: n.x, top: n.y, width: NODE_W, height: NODE_H,
                  background: 'linear-gradient(180deg, color-mix(in srgb, var(--color-panel2) 82%, white 1%), color-mix(in srgb, var(--color-panel2) 96%, #000 2%))',
                  borderColor: sel ? 'rgb(var(--primary-rgb))' : 'color-mix(in srgb, rgb(var(--primary-rgb)) 42%, white 3%)',
                  cursor: 'grab',
                }}
                onPointerDown={(e) => startDrag(e, n.id)}
                onPointerMove={onPointerMove}
                onPointerUp={onPointerUp}
                onClick={() => onSelect?.(n.id)}
              >
                <div className="flex items-start justify-between gap-1">
                  <div className="min-w-0">
                    <div className="truncate text-[12px] font-bold text-ink">{n.label}</div>
                    <div className="mt-0.5 text-[10px] text-muted">{n.meta || n.kind}</div>
                  </div>
                  <button
                    type="button"
                    onPointerDown={(e) => e.stopPropagation()}
                    onClick={(e) => { e.stopPropagation(); startConnect(e as unknown as React.PointerEvent, n.id) }}
                    onPointerMove={onPointerMove}
                    onPointerUp={onPointerUp}
                    title="拖出连线"
                    aria-label={`从 ${n.label} 连线`}
                    className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-secondary/50 bg-panel2 text-secondary hover:border-secondary"
                  >
                    <Plus size={10} />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* save / publish / run — honest when the real contract is not wired */}
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" onClick={onRun} aria-label="运行" disabled={runDisabled} className="rounded-lg border border-border bg-panel2/72 px-3.5 py-2 text-[12px] font-semibold text-ink hover:border-primary/40 disabled:opacity-40">运行</button>
        <button type="button" onClick={onPublish} aria-label="保存并发布" disabled={publishDisabled} className="rounded-lg bg-gradient-to-br from-primary to-secondary px-3.5 py-2 text-[12px] font-bold text-white shadow-card hover:scale-[1.01] disabled:opacity-40">保存并发布</button>
        {(publishHint || runHint) ? (
          <span className="text-[11px] text-muted">{publishHint || runHint}</span>
        ) : null}
      </div>
    </div>
  )
}

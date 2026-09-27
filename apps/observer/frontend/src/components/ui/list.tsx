// L10 (2026-09-27): B04 `.list` / `.list-item` + Timeline variant —
// dense read-only rows with hover lift (L6 120ms). B10 `.list-item`:
// surface2 background, 14px radius, title + small muted sub + optional
// right-hand state pill. Timeline = same rows with a leading time column.
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import type { BadgeVariant } from './badge'
import { StatusPill } from './status'

export interface ListItem {
  title: ReactNode
  /** muted secondary line */
  sub?: ReactNode
  /** right-side state pill */
  state?: { text: string; variant?: BadgeVariant }
  /** optional leading mono column (timeline time / execution id) */
  leading?: ReactNode
}

export function ListView({ items, className }: { items: ListItem[]; className?: string }) {
  return (
    <div className={cn('flex flex-col gap-2.5', className)}>
      {items.map((it, i) => (
        <div
          key={i}
          className={cn(
            'panel2 wl-card-hover flex items-center justify-between gap-3 rounded-lg border border-border/68 px-3.5 py-3',
            'transition-[transform,border-color,box-shadow] duration-fast hover:-translate-y-px',
          )}
        >
          <div className="flex min-w-0 items-center gap-3">
            {it.leading ? (
              <span className="shrink-0 font-mono text-[11px] text-muted tabular-nums">{it.leading}</span>
            ) : null}
            <div className="min-w-0">
              <div className="text-[13px] font-medium text-ink truncate">{it.title}</div>
              {it.sub != null ? <div className="mt-0.5 text-[11px] text-muted truncate">{it.sub}</div> : null}
            </div>
          </div>
          {it.state ? <StatusPill variant={it.state.variant ?? 'muted'}>{it.state.text}</StatusPill> : null}
        </div>
      ))}
    </div>
  )
}

export function Timeline({ items, className }: { items: ListItem[]; className?: string }) {
  return (
    <div className={cn('relative flex flex-col gap-2.5 pl-4', className)}>
      <div className="absolute left-1 top-2 bottom-2 w-px bg-border/60" aria-hidden="true" />
      {items.map((it, i) => (
        <div key={i} className="relative">
          <span className="absolute -left-[13px] top-1/2 h-2 w-2 -translate-y-1/2 rounded-full bg-primary shadow-[0_0_8px_var(--glow-primary)]" aria-hidden="true" />
          <ListView items={[it]} className="px-2" />
        </div>
      ))}
    </div>
  )
}

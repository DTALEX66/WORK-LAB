// L10 (2026-09-27): B10 `.status-stack` pills + `.tag` gradient status
// badges. Two contracts:
//  - StatusDot: the transport-style state dot (live pulse) + optional label
//  - StatusPill: a colored state pill (success/warning/error/info/muted),
//    1:1 of B10 `.tag` (rounded-full, 12px bold, gradient fill)
import * as React from 'react'
import { cn } from '@/lib/utils'
import type { BadgeVariant } from './badge'

export function StatusPill({
  variant = 'muted',
  children,
  className,
}: {
  variant?: BadgeVariant
  children: React.ReactNode
  className?: string
}) {
  const fills: Record<BadgeVariant, string> = {
    success: 'bg-gradient-to-br from-[#27c86a] to-[#11a74d] text-white',
    warning: 'bg-gradient-to-br from-[#f2b541] to-[#c98c00] text-white',
    error: 'bg-gradient-to-br from-[#f86b6b] to-[#cb3e3e] text-white',
    info: 'bg-gradient-to-br from-primary to-secondary text-white',
    muted: 'bg-panel2 text-muted border border-border/60',
  }
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[12px] font-bold whitespace-nowrap',
        fills[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}

export function StatusDot({
  state,
  label,
  pulse = false,
  className,
}: {
  /** transport-style truth: LIVE/ONLINE green, DEGRADED warning, OFFLINE/ERROR red, unknown gray */
  state: 'live' | 'degraded' | 'offline' | 'unknown'
  label?: string
  pulse?: boolean
  className?: string
}) {
  const color =
    state === 'live' ? 'bg-success' :
    state === 'degraded' ? 'bg-warning' :
    state === 'offline' ? 'bg-error' : 'bg-zinc-500'
  return (
    <span className={cn('inline-flex items-center gap-2', className)}>
      <span
        className={cn('h-2 w-2 shrink-0 rounded-full', color, pulse && 'status-pulse')}
        aria-hidden="true"
      />
      {label ? <span className="text-[11px] text-muted">{label}</span> : null}
    </span>
  )
}

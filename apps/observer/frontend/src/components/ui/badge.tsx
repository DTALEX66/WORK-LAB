import * as React from 'react'
import { cn } from '@/lib/utils'

type BadgeVariant = 'success' | 'warning' | 'error' | 'info' | 'muted'

const variants: Record<BadgeVariant, string> = {
  success: 'bg-success/10 text-success border-success/20',
  warning: 'bg-warning/10 text-warning border-warning/20',
  error: 'bg-error/10 text-error border-error/20',
  info: 'bg-primary/10 text-primary border-primary/20',
  muted: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
}

export function Badge({ variant = 'muted', className, children, ...props }: React.HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-[11px] font-medium border', variants[variant], className)} {...props}>
      {children}
    </span>
  )
}

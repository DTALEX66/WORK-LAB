// L10 (2026-09-27): B06 hover Tooltip — pure-CSS/JS, no dependency.
// 120ms hover reveal (L6 motion-fast), z-index from the B10 token layer
// (.z-tooltip). Usage: <Tooltip text="…"><Button/></Tooltip>
import * as React from 'react'
import { cn } from '@/lib/utils'

export interface TooltipProps {
  text: string
  side?: 'top' | 'bottom'
  children: React.ReactNode
  className?: string
}

export function Tooltip({ text, side = 'top', children, className }: TooltipProps) {
  return (
    <span
      className={cn('group/tt relative inline-flex', className)}
      aria-label={text}
    >
      {children}
      <span
        role="tooltip"
        className={cn(
          'pointer-events-none absolute left-1/2 -translate-x-1/2 z-tooltip whitespace-nowrap',
          'rounded-md border border-border bg-panel2 px-2.5 py-1.5 text-[11px] text-ink shadow-card',
          'opacity-0 transition-opacity duration-fast group-hover/tt:opacity-100',
          side === 'top' ? 'bottom-full mb-1.5' : 'top-full mt-1.5',
        )}
      >
        {text}
      </span>
    </span>
  )
}

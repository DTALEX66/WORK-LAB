// L10 (2026-09-27): shared B10 page header — 1:1 of the B10 `.page-head`
// structure: large title + muted description on the left, primary/secondary
// actions on the right. Every L7 page-matrix page renders through this
// component; per-page actions are passed in (disabled/honest when the real
// contract is not wired yet).
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface PageHeaderProps {
  title: string
  description?: string
  /** page actions, rendered right-aligned */
  actions?: ReactNode
  className?: string
}

export function PageHeader({ title, description, actions, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        'flex flex-wrap items-start justify-between gap-x-6 gap-y-3 mb-5',
        className,
      )}
    >
      <div className="min-w-0">
        <h2 className="text-[26px] leading-tight font-semibold tracking-tight text-ink m-0">
          {title}
        </h2>
        {description ? (
          <p className="text-xs text-muted mt-1.5 m-0 max-w-2xl leading-relaxed">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2.5 shrink-0">{actions}</div> : null}
    </div>
  )
}

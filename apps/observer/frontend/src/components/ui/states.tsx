import * as React from 'react'
import { Loader2, CloudOff, Inbox, TriangleAlert } from 'lucide-react'
import { Button } from './button'
import { cn } from '@/lib/utils'

/**
 * UI_COMPONENTS (20260921): the five L7 view-state contracts as reusable
 * shells. These are HONEST states — they render real placeholders, never
 * fabricated KPIs. The view supplies the actual message (e.g. "快照未携带
 * 治理契约明细").
 */
export interface EmptyStateProps {
  title: string
  description?: string
  /** optional call-to-action button (rendered when provided) */
  action?: React.ReactNode
  className?: string
}

export function EmptyState({ title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'panel flex flex-col items-center justify-center gap-3 px-6 py-12 text-center min-h-[240px]',
        className,
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-panel2 text-muted">
        <Inbox className="h-5 w-5" aria-hidden="true" />
      </div>
      <div>
        <p className="text-sm font-medium text-ink">{title}</p>
        {description ? <p className="mt-1 text-xs text-muted max-w-md mx-auto">{description}</p> : null}
      </div>
      {action ? <div className="mt-1">{action}</div> : null}
    </div>
  )
}

export interface LoadingSkeletonProps {
  rows?: number
  className?: string
}

export function LoadingSkeleton({ rows = 4, className }: LoadingSkeletonProps) {
  return (
    <div className={cn('panel px-4 py-4 space-y-3', className)} role="status" aria-label="加载中">
      <span className="sr-only">加载中…</span>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="h-4 w-4 rounded bg-panel2 animate-pulse" />
          <div className="h-3 flex-1 rounded bg-panel2 animate-pulse" />
          <div className="h-3 w-16 rounded bg-panel2 animate-pulse" />
        </div>
      ))}
    </div>
  )
}

export interface ErrorStateProps {
  message: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({ message, onRetry, className }: ErrorStateProps) {
  return (
    <div
      className={cn(
        'panel flex flex-col items-center justify-center gap-3 px-6 py-12 text-center min-h-[240px] border-error/40',
        className,
      )}
      role="alert"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-error/10 text-error">
        <TriangleAlert className="h-5 w-5" aria-hidden="true" />
      </div>
      <div>
        <p className="text-sm font-medium text-ink">无法加载</p>
        {message ? <p className="mt-1 text-xs text-muted max-w-md mx-auto break-words">{message}</p> : null}
      </div>
      {onRetry ? <Button variant="ghost" size="sm" onClick={onRetry}>重试</Button> : null}
    </div>
  )
}

export function OfflineState({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'panel flex flex-col items-center justify-center gap-3 px-6 py-12 text-center min-h-[240px]',
        className,
      )}
      role="status"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-warning/10 text-warning">
        <CloudOff className="h-5 w-5" aria-hidden="true" />
      </div>
      <div>
        <p className="text-sm font-medium text-ink">连接中断</p>
        <p className="mt-1 text-xs text-muted">后端快照不可达，正在等待重连…</p>
      </div>
      <Loader2 className="h-4 w-4 animate-spin text-muted" aria-hidden="true" />
    </div>
  )
}

export interface UnknownStateProps {
  title?: string
  description?: string
  className?: string
}

export function UnknownState({
  title = '数据未知',
  description,
  className,
}: UnknownStateProps) {
  return (
    <div
      className={cn(
        'panel flex flex-col items-center justify-center gap-3 px-6 py-12 text-center min-h-[240px]',
        className,
      )}
      role="status"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-panel2 text-muted">
        <Inbox className="h-5 w-5" aria-hidden="true" />
      </div>
      <div>
        <p className="text-sm font-medium text-ink">{title}</p>
        {description ? <p className="mt-1 text-xs text-muted max-w-md mx-auto">{description}</p> : null}
      </div>
    </div>
  )
}

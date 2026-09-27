import * as React from 'react'
import { Loader2, CloudOff, Inbox, TriangleAlert } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * UI_COMPONENTS (20260921) · L10b (2026-09-27): the five L7 view-state
 * contracts as reusable shells. These are HONEST states — they render real
 * placeholders, never fabricated KPIs; the view supplies the actual message
 * (e.g. "快照未携带治理契约明细").
 *
 * L10b: the visual shell is the B10 `.empty` block verbatim —
 *   .empty            text-align:center; padding:56px 20px; color:muted
 *   .empty .icon      64px circle, primary border + primary glyph + glow
 * Titles keep the repo's text contract; the icon slot is a div (not an SVG)
 * so the B10 child selector `.empty .icon` matches.
 */
function StateShell({
  icon,
  title,
  description,
  action,
  className,
  role,
}: {
  icon: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
  role?: string
}) {
  return (
    <div className={cn('empty', className)} role={role}>
      <div className="icon" aria-hidden="true">{icon}</div>
      <div>
        <p className="text-sm font-semibold text-ink">{title}</p>
        {description ? <p className="mx-auto mt-1 max-w-xl text-xs">{description}</p> : null}
      </div>
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  )
}

export interface EmptyStateProps {
  title: string
  description?: string
  /** optional call-to-action button (rendered when provided) */
  action?: React.ReactNode
  className?: string
}

export function EmptyState({ title, description, action, className }: EmptyStateProps) {
  return (
    <StateShell
      icon={<Inbox size={26} strokeWidth={1.8} />}
      title={title}
      description={description}
      action={action}
      className={className}
    />
  )
}

export interface LoadingSkeletonProps {
  rows?: number
  className?: string
}

export function LoadingSkeleton({ rows = 4, className }: LoadingSkeletonProps) {
  return (
    <div className={cn('panel', className)} role="status" aria-label="加载中">
      <span className="sr-only">加载中…</span>
      <div className="flex flex-col gap-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="h-4 w-4 rounded bg-panel2 animate-pulse" />
            <div className="h-3 flex-1 rounded bg-panel2 animate-pulse" />
            <div className="h-3 w-16 rounded bg-panel2 animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  )
}

export interface ErrorStateProps {
  message: string
  className?: string
}

/**
 * ErrorState is a pure message surface. L10b removed the optional 重试 action:
 * Observer is strictly read-only, so no state component may hand a caller a
 * retry/write affordance (Observer §8 iron law) — a failed read is reported,
 * not re-driven from a projection page.
 */
export function ErrorState({ message, className }: ErrorStateProps) {
  return (
    <StateShell
      icon={<TriangleAlert size={26} strokeWidth={1.8} />}
      title="无法加载"
      description={message}
      className={className}
      role="alert"
    />
  )
}

export function OfflineState({ className }: { className?: string }) {
  return (
    <StateShell
      icon={<CloudOff size={26} strokeWidth={1.8} />}
      title="连接中断"
      description="后端快照不可达，正在等待重连…"
      action={<Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
      className={className}
      role="status"
    />
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
    <StateShell
      icon={<Inbox size={26} strokeWidth={1.8} />}
      title={title}
      description={description}
      className={className}
      role="status"
    />
  )
}

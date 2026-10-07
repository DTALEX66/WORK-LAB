import * as React from 'react'
import { Loader2, CloudOff, Inbox, TriangleAlert, Lock } from 'lucide-react'
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

// M-2 (UI-CHECK-20261006): LoadingSkeleton is gone. It had zero callers, and the
// shell settled on a load strip instead (App.tsx `loadingStrip`) because the B5
// rule pins every KPI to UNKNOWN with no snapshot — a skeleton that *replaces*
// content hides exactly the state that rule defends. Keeping an unused skeleton
// in the design system invited the other implementation: it is the one loading
// affordance whose presence would make a real UNKNOWN invisible.

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

export interface PermissionStateProps {
  /** what the user cannot do here, in one line */
  blocked: string
  /** WHY it is blocked: the contract or permission that owns the write */
  reason: string
  /** what this surface still does, so the reader is not left with a dead end */
  stillAvailable?: string
  title?: string
  className?: string
}

/**
 * PERMISSION / READ-ONLY state (UI prompt pack G1).
 *
 * Distinct from UnknownState on purpose: UNKNOWN says "the projection has no
 * value", this says "the value may be known and this surface still cannot act".
 * The prompt pack forbids a write action that merely looks available, so a
 * read-only lane has to name the owner of the write rather than go quiet.
 */
export function PermissionState({
  blocked,
  reason,
  stillAvailable,
  title = '此界面只读',
  className,
}: PermissionStateProps) {
  return (
    <StateShell
      icon={<Lock size={26} strokeWidth={1.8} />}
      title={title}
      description={
        [blocked, reason, stillAvailable].filter(Boolean).join(' — ')
      }
      className={className}
      role="status"
    />
  )
}
